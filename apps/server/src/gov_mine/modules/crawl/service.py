"""The crawl: starting a run from the homepage and the sitemap, fetching a page into the fetch
log (once its host's robots.txt allows it, and its delay has passed) and queueing the links it
holds one link deeper, and finishing the run when its jobs are done. The jobs in jobs.py call
these, one transaction each."""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlsplit

import httpx
from procrastinate.types import JSONValue
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.db.base import utcnow
from gov_mine.integrations.http import ROBOT_NAME
from gov_mine.integrations.storage import ObjectStore
from gov_mine.jobs import registry
from gov_mine.jobs.tasks import defer
from gov_mine.modules.crawl.models import (
    DEFAULT_CRAWL_DELAY_MS,
    CrawlPolicy,
    CrawlRun,
    Domain,
    Fetch,
    FetchOutcome,
    RunStatus,
    Webpage,
)
from gov_mine.modules.ingest import service as ingest
from gov_mine.modules.institutions.models import Institution
from gov_mine.shared.exceptions import NotFoundError
from gov_mine.shared.robots import robots_allows, robots_crawl_delay, robots_url
from gov_mine.shared.sitemaps import parse_sitemap
from gov_mine.shared.urls import find_links, is_within, looks_like_file, normalise_url

logger = logging.getLogger(__name__)

START_TASK = "crawl.start"
FETCH_TASK = "crawl.fetch"
FINISH_TASK = "crawl.finish"
# How long `crawl.finish` waits before it looks again at a run that still has work queued.
FINISH_POLL = timedelta(seconds=3)

DEFAULT_MEDIA_TYPE = "application/octet-stream"
HTML_MEDIA_TYPES = frozenset({"text/html", "application/xhtml+xml"})
# A URL more than this many links from a seed is not fetched (decision 31): it stops crawler
# traps such as endless calendars.
MAX_DEPTH = 50
# The longest URL `webpages.url` holds; a longer link is not followed.
MAX_URL_LENGTH = 2048
# Where a run looks for the host's sitemap.
SITEMAP_PATH = "/sitemap.xml"
# The most sitemap files a run reads, the index included: an index can point to thousands.
MAX_SITEMAPS = 50

# How the crawl waits out a host's delay. Tests that are not about pacing swap it for one that
# does not wait.
sleep = asyncio.sleep

# Whether any job of the run other than `crawl.finish` is waiting or running. Every job of a
# run carries its `run_id`; a job queues its follow-ups in its own transaction, before it is
# marked done, so a run with work left always has a job in one of the two states.
_RUN_HAS_WORK = text(
    "SELECT EXISTS (SELECT 1 FROM procrastinate_jobs"
    " WHERE status IN ('todo', 'doing') AND task_name <> :finish AND args->>'run_id' = :run_id)"
)
# The webpages among :ids the run has already queued or attempted: a fetch job in any state, or
# a fetches row (a finished job's row is gone from the queue).
_IN_RUN = text(
    "SELECT webpage_id FROM fetches"
    " WHERE crawl_run_id = :run_id AND webpage_id = ANY(:ids)"
    " UNION SELECT (args->>'webpage_id')::uuid FROM procrastinate_jobs"
    " WHERE task_name = :fetch AND args->>'run_id' = :run_key"
    " AND (args->>'webpage_id')::uuid = ANY(:ids)"
)
# Requests the run has sent: a refusal's row has no duration.
_REQUESTS_SENT = select(func.count()).select_from(Fetch).where(Fetch.duration_ms.is_not(None))


def host_of(url: str) -> str:
    """The lower-cased host, without port or credentials."""
    host = urlsplit(url).hostname
    if not host:
        raise ValueError(f"not an absolute URL: {url!r}")
    return host


def media_type_of(response: httpx.Response) -> str:
    """The `Content-Type` without its parameters, lower-cased."""
    value = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    return value or DEFAULT_MEDIA_TYPE


async def ensure_domain(session: AsyncSession, name: str, policy: CrawlPolicy) -> Domain:
    """The domain row for host `name`, created with `policy` if there is none. An existing
    row keeps its policy. It is looked up before the insert: an insert that conflicts with a
    row another job is updating (its robots.txt) waits for that job, which may be waiting
    for this one's run lock."""
    query = select(Domain).where(Domain.name == name)
    domain = await session.scalar(query)
    if domain is None:
        await session.execute(
            insert(Domain).values(name=name, crawl_policy=policy).on_conflict_do_nothing()
        )
        domain = (await session.scalars(query)).one()
    return domain


async def ensure_webpage(session: AsyncSession, url: str, domain_id: uuid.UUID) -> Webpage:
    """The webpage row for normalised `url`, created if there is none."""
    await session.execute(
        insert(Webpage).values(url=url, domain_id=domain_id).on_conflict_do_nothing()
    )
    return (await session.scalars(select(Webpage).where(Webpage.url == url))).one()


async def lock_run(session: AsyncSession, run_id: uuid.UUID) -> None:
    """Hold the run's lock until the transaction ends, so two of its fetch jobs neither queue
    the same URL nor both send the request that reaches `--limit`."""
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:run_id, 0))"), {"run_id": str(run_id)}
    )


async def get_run(session: AsyncSession, run_id: uuid.UUID) -> CrawlRun:
    run = await session.get(CrawlRun, run_id)
    if run is None:
        raise NotFoundError(f"No run {run_id}")
    return run


async def queue(
    session: AsyncSession,
    task_name: str,
    *,
    schedule_in: timedelta | None = None,
    lock: str | None = None,
    **kwargs: JSONValue,
) -> int:
    """One of the crawl's jobs, in `session`'s transaction."""
    return await defer(
        session, registry.tasks[task_name], schedule_in=schedule_in, lock=lock, **kwargs
    )


async def queue_fetch(
    session: AsyncSession, run_id: uuid.UUID, webpage: uuid.UUID, domain: uuid.UUID, depth: int
) -> int:
    """A `crawl.fetch` of `webpage` at `depth`, locked by its domain, so the host's fetches run
    one at a time, in the order they were queued, however many workers there are."""
    return await queue(
        session,
        FETCH_TASK,
        lock=str(domain),
        run_id=str(run_id),
        webpage_id=str(webpage),
        depth=depth,
    )


async def wait_for_host(session: AsyncSession, domain_id: uuid.UUID) -> datetime:
    """Wait until the host's `crawl_delay_ms` has passed since its last request, then note now
    as its last request and return it: call it right before sending one. The domain row stays
    locked until the transaction ends, so a job outside the fetch lock (`crawl.start`) cannot
    send the host a request meanwhile either."""
    domain = (
        await session.scalars(
            select(Domain)
            .where(Domain.id == domain_id)
            # Not FOR UPDATE: it would hold back the webpages inserted for this host.
            .with_for_update(key_share=True)
            .execution_options(populate_existing=True)
        )
    ).one()
    if domain.last_request_at is not None:
        due = domain.last_request_at + timedelta(milliseconds=domain.crawl_delay_ms)
        wait = (due - utcnow()).total_seconds()
        if wait > 0:
            await sleep(wait)
    sent = domain.last_request_at = utcnow()
    await session.flush()
    return sent


async def start_run(session: AsyncSession, http: httpx.AsyncClient, run_id: uuid.UUID) -> None:
    """Mark a queued run running and queue its seeds at depth 0: the institution's homepage, on
    its own host as a `crawl` domain, then every page the host's sitemap lists. Then queue
    `crawl.finish`, which waits for the run's jobs."""
    run = await get_run(session, run_id)
    if run.status is not RunStatus.QUEUED:
        logger.info("Run %s is %s, not queued: not started again", run.id, run.status)
        return
    institution = await session.get_one(Institution, run.institution_id)
    run.status = RunStatus.RUNNING
    run.started_at = utcnow()
    homepage_url = normalise_url(institution.website_url)
    domain = await ensure_domain(session, host_of(homepage_url), CrawlPolicy.CRAWL)
    homepage = await ensure_webpage(session, homepage_url, domain.id)
    await queue_fetch(session, run.id, homepage.id, domain.id, 0)
    seeds = await read_sitemap(session, http, domain.id, homepage_url)
    queued = await queue_links(session, run.id, None, seeds, 0)
    logger.info("Run %s seeded with the homepage and %d sitemap URLs", run.id, queued)
    await queue(session, FINISH_TASK, run_id=str(run.id))


async def read_sitemap(
    session: AsyncSession, http: httpx.AsyncClient, domain_id: uuid.UUID, homepage_url: str
) -> list[str]:
    """The normalised page URLs listed by `/sitemap.xml` on the homepage's host (its domain is
    `domain_id`), and, when it is an index, by the sitemap files it points to on the same host,
    each once, paced like any request to the host. A file that is missing, fails, or is not a
    sitemap adds nothing; at most `MAX_SITEMAPS` files are read."""
    host = host_of(homepage_url)
    pending = [urljoin(homepage_url, SITEMAP_PATH)]
    seen = set(pending)
    pages: dict[str, None] = {}
    for _ in range(MAX_SITEMAPS):
        if not pending:
            break
        url = pending.pop(0)
        await wait_for_host(session, domain_id)
        try:
            response = await http.get(url)
        except httpx.HTTPError as exc:
            logger.warning("Sitemap %s not read: %s", url, type(exc).__name__)
            continue
        if response.status_code != httpx.codes.OK:
            logger.info("Sitemap %s not read: HTTP %d", url, response.status_code)
            continue
        try:
            sitemap = parse_sitemap(response.content)
        except ValueError as exc:
            logger.warning("Sitemap %s not read: %s", url, exc)
            continue
        for location in sitemap.sitemaps:
            child = _normalised(location)
            if child is not None and host_of(child) == host and child not in seen:
                seen.add(child)
                pending.append(child)
        pages |= {page: None for location in sitemap.pages if (page := _normalised(location))}
    return list(pages)


def _normalised(url: str) -> str | None:
    try:
        return normalise_url(url)
    except ValueError:
        return None


def refusal(
    url: str, policy: CrawlPolicy, website_url: str, depth: int
) -> tuple[FetchOutcome, str] | None:
    """Why the fence turns `url`, on a host with `policy`, down at `depth`, as an outcome and a
    reason, or None. A `blocked` host is never fetched, and a `files_only` host only for what
    looks like a file. The institution's website prefix bounds its own host; any other `crawl`
    host is in scope whole."""
    if policy is CrawlPolicy.BLOCKED:
        return FetchOutcome.SKIPPED_SCOPE, "blocked_host"
    if policy is CrawlPolicy.PLATFORM:
        # No platform rule exists yet to say which of its URLs to follow.
        return FetchOutcome.SKIPPED_SCOPE, "platform_host"
    if policy is CrawlPolicy.FILES_ONLY and not looks_like_file(url):
        return FetchOutcome.SKIPPED_SCOPE, "not_a_file"
    prefix = normalise_url(website_url)
    if host_of(url) == host_of(prefix) and not is_within(url, prefix):
        return FetchOutcome.SKIPPED_SCOPE, "outside_prefix"
    if depth > MAX_DEPTH:
        return FetchOutcome.SKIPPED_DEPTH, f"depth {depth} > {MAX_DEPTH}"
    return None


async def robots_refusal(
    session: AsyncSession, http: httpx.AsyncClient, run: CrawlRun, domain: Domain, url: str
) -> tuple[FetchOutcome, str] | None:
    """Why the host's robots.txt turns `url` down, or None. The first URL on a host in a run
    reads its robots.txt into the domain row, under the row's lock, so the other jobs of the
    run find it there; a robots.txt that could not be read refuses every URL on the host."""
    if _robots_stale(domain, run):
        domain = (
            await session.scalars(
                select(Domain)
                .where(Domain.id == domain.id)
                # Not FOR UPDATE: it would hold back the webpages inserted for this host.
                .with_for_update(key_share=True)
                .execution_options(populate_existing=True)
            )
        ).one()
        if _robots_stale(domain, run):
            await wait_for_host(session, domain.id)
            await read_robots(http, domain, url)
    if domain.robots_txt is None:
        return FetchOutcome.BLOCKED_ROBOTS, "robots_unreachable"
    if not robots_allows(domain.robots_txt, url, ROBOT_NAME):
        return FetchOutcome.BLOCKED_ROBOTS, "disallowed"
    return None


def _robots_stale(domain: Domain, run: CrawlRun) -> bool:
    """Whether the run has not read the host's robots.txt yet."""
    fetched = domain.robots_fetched_at
    return fetched is None or (run.started_at is not None and fetched < run.started_at)


async def read_robots(http: httpx.AsyncClient, domain: Domain, url: str) -> None:
    """Read the robots.txt governing `url` into `domain`, following redirects, and set the
    host's delay from it. A 4xx is no robots.txt: stored as "", every path is allowed. A 5xx
    or a failed request stores None, which refuses every path until the next run reads it
    again (RFC 9309, "unreachable")."""
    location = robots_url(url)
    try:
        response = await http.get(location, follow_redirects=True)
    except httpx.HTTPError as exc:
        logger.warning("robots.txt %s not read: %s", location, type(exc).__name__)
        domain.robots_txt = None
    else:
        if response.status_code == httpx.codes.OK:
            domain.robots_txt = response.text
        elif response.is_client_error:
            logger.info("robots.txt %s: HTTP %d, all allowed", location, response.status_code)
            domain.robots_txt = ""
        else:
            logger.warning("robots.txt %s not read: HTTP %d", location, response.status_code)
            domain.robots_txt = None
    domain.robots_fetched_at = utcnow()
    delay = robots_crawl_delay(domain.robots_txt or "", ROBOT_NAME)
    domain.crawl_delay_ms = max(DEFAULT_CRAWL_DELAY_MS, round((delay or 0) * 1000))


async def fetch_page(  # noqa: PLR0913 - the job's three arguments and what it works with
    session: AsyncSession,
    http: httpx.AsyncClient,
    store: ObjectStore,
    *,
    run_id: uuid.UUID,
    webpage_id: uuid.UUID,
    depth: int,
) -> Fetch | None:
    """Fetch a webpage found `depth` links from a seed and log the attempt as a `fetches` row.

    Once the run has sent its `--limit` requests, nothing happens and None is returned. A URL
    the fence or the host's robots.txt refuses gets its row and no request; reading robots.txt
    writes no row and does not count toward `--limit`. Otherwise a 200 hands the body to
    `ingest.store`: `fetched` with the new snapshot, or `unchanged` when the bytes are the ones
    already kept; an HTML page on a `crawl` host then queues its links one link deeper (what a
    `files_only` host serves is never followed, whatever its type). Any other status is
    `failed_http`, and a timeout `failed_timeout`. A request, robots.txt's included, first waits
    out the host's delay; a sent request's `requested_at` is when it was sent."""
    run = await get_run(session, run_id)
    limit = run.settings.get("limit")
    if limit is not None:
        await lock_run(session, run.id)
        sent = await session.scalar(_REQUESTS_SENT.where(Fetch.crawl_run_id == run.id)) or 0
        if sent >= limit:
            logger.info("Run %s has sent its %d requests: not fetched", run.id, limit)
            return None
    institution = await session.get_one(Institution, run.institution_id)
    webpage = await session.get_one(Webpage, webpage_id)
    domain = await session.get_one(Domain, webpage.domain_id)
    fetch = Fetch(crawl_run_id=run.id, webpage_id=webpage.id, requested_at=utcnow())
    refused = refusal(webpage.url, domain.crawl_policy, institution.website_url, depth)
    if refused is None:
        refused = await robots_refusal(session, http, run, domain, webpage.url)
    if refused is not None:
        fetch.outcome, fetch.reason = refused
        session.add(fetch)
        await session.flush()
        return fetch
    fetch.requested_at = await wait_for_host(session, domain.id)
    started = time.perf_counter()
    try:
        response = await http.get(webpage.url)
    except httpx.TimeoutException as exc:
        fetch.duration_ms = _ms_since(started)
        fetch.outcome = FetchOutcome.FAILED_TIMEOUT
        fetch.reason = type(exc).__name__
    else:
        fetch.duration_ms = _ms_since(started)
        fetch.http_status = response.status_code
        if response.status_code == httpx.codes.OK:
            fetch.snapshot_id = await ingest.store(
                session, store, webpage.id, response.content, media_type_of(response)
            )
            fetch.outcome = (
                FetchOutcome.FETCHED if fetch.snapshot_id is not None else FetchOutcome.UNCHANGED
            )
            if (
                domain.crawl_policy is CrawlPolicy.CRAWL
                and media_type_of(response) in HTML_MEDIA_TYPES
            ):
                links = find_links(response.text, webpage.url)
                await queue_links(session, run.id, webpage, links, depth + 1)
        else:
            fetch.outcome = FetchOutcome.FAILED_HTTP
    session.add(fetch)
    await session.flush()
    return fetch


async def queue_links(
    session: AsyncSession,
    run_id: uuid.UUID,
    found_on: Webpage | None,
    urls: list[str],
    depth: int,
) -> int:
    """Queue a fetch at `depth` for each normalised URL in `urls` the run has not queued yet.
    A URL seen for the first time gets its webpage row, found on `found_on` (None for a seed);
    a host seen for the first time, its domain as `files_only`. Returns how many were queued."""
    urls = [url for url in urls if len(url) <= MAX_URL_LENGTH]
    if not urls:
        return 0
    await lock_run(session, run_id)
    domains = {
        host: (await ensure_domain(session, host, CrawlPolicy.FILES_ONLY)).id
        for host in {host_of(url) for url in urls}
    }
    await session.execute(
        insert(Webpage).on_conflict_do_nothing(),
        [
            {
                "url": url,
                "domain_id": domains[host_of(url)],
                "discovered_from_webpage_id": found_on.id if found_on else None,
            }
            for url in urls
        ],
    )
    found = await session.execute(select(Webpage.url, Webpage.id).where(Webpage.url.in_(urls)))
    ids: dict[str, uuid.UUID] = dict(found.all())
    in_run = set(
        await session.scalars(
            _IN_RUN,
            {
                "run_id": run_id,
                "run_key": str(run_id),
                "ids": list(ids.values()),
                "fetch": FETCH_TASK,
            },
        )
    )
    queued = 0
    for url in urls:
        if ids[url] in in_run:
            continue
        in_run.add(ids[url])
        await queue_fetch(session, run_id, ids[url], domains[host_of(url)], depth)
        queued += 1
    return queued


async def finish_run(session: AsyncSession, run_id: uuid.UUID) -> bool:
    """Mark a running run `finished` once none of its jobs is waiting or running; until then,
    queue another look in `FINISH_POLL`. True when the run was finished."""
    run = await get_run(session, run_id)
    if run.status is not RunStatus.RUNNING:
        return False
    if await session.scalar(_RUN_HAS_WORK, {"finish": FINISH_TASK, "run_id": str(run.id)}):
        await queue(session, FINISH_TASK, schedule_in=FINISH_POLL, run_id=str(run.id))
        return False
    run.status = RunStatus.FINISHED
    run.finished_at = utcnow()
    return True


def _ms_since(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


__all__ = [
    "FETCH_TASK",
    "FINISH_POLL",
    "FINISH_TASK",
    "MAX_DEPTH",
    "START_TASK",
    "ensure_domain",
    "ensure_webpage",
    "fetch_page",
    "finish_run",
    "get_run",
    "host_of",
    "lock_run",
    "media_type_of",
    "queue",
    "queue_fetch",
    "queue_links",
    "read_robots",
    "read_sitemap",
    "refusal",
    "robots_refusal",
    "start_run",
    "wait_for_host",
]
