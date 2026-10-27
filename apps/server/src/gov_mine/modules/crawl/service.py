"""The crawl: starting a run, fetching a page into the fetch log, and finishing the run when its
jobs are done. The jobs in jobs.py call these, one transaction each."""

import logging
import time
import uuid
from datetime import timedelta
from urllib.parse import urlsplit

import httpx
from procrastinate.types import JSONValue
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.db.base import utcnow
from gov_mine.integrations.storage import ObjectStore
from gov_mine.jobs import registry
from gov_mine.jobs.tasks import defer
from gov_mine.modules.crawl.models import (
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

logger = logging.getLogger(__name__)

START_TASK = "crawl.start"
FETCH_TASK = "crawl.fetch"
FINISH_TASK = "crawl.finish"
# How long `crawl.finish` waits before it looks again at a run that still has work queued.
FINISH_POLL = timedelta(seconds=3)

DEFAULT_MEDIA_TYPE = "application/octet-stream"

# Whether any job of the run other than `crawl.finish` is waiting or running. Every job of a
# run carries its `run_id`; a job queues its follow-ups in its own transaction, before it is
# marked done, so a run with work left always has a job in one of the two states.
_RUN_HAS_WORK = text(
    "SELECT EXISTS (SELECT 1 FROM procrastinate_jobs"
    " WHERE status IN ('todo', 'doing') AND task_name <> :finish AND args->>'run_id' = :run_id)"
)


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
    row keeps its policy."""
    await session.execute(
        insert(Domain).values(name=name, crawl_policy=policy).on_conflict_do_nothing()
    )
    return (await session.scalars(select(Domain).where(Domain.name == name))).one()


async def ensure_webpage(session: AsyncSession, url: str, domain_id: uuid.UUID) -> Webpage:
    await session.execute(
        insert(Webpage).values(url=url, domain_id=domain_id).on_conflict_do_nothing()
    )
    return (await session.scalars(select(Webpage).where(Webpage.url == url))).one()


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
    **kwargs: JSONValue,
) -> int:
    """One of the crawl's jobs, in `session`'s transaction."""
    return await defer(session, registry.tasks[task_name], schedule_in=schedule_in, **kwargs)


async def start_run(session: AsyncSession, run_id: uuid.UUID) -> None:
    """Mark a queued run running and queue its seed: the institution's homepage, on its own
    host as a `crawl` domain. Then queue `crawl.finish`, which waits for the run's jobs."""
    run = await get_run(session, run_id)
    if run.status is not RunStatus.QUEUED:
        logger.info("Run %s is %s, not queued: not started again", run.id, run.status)
        return
    institution = await session.get_one(Institution, run.institution_id)
    run.status = RunStatus.RUNNING
    run.started_at = utcnow()
    domain = await ensure_domain(session, host_of(institution.website_url), CrawlPolicy.CRAWL)
    homepage = await ensure_webpage(session, institution.website_url, domain.id)
    await queue(session, FETCH_TASK, run_id=str(run.id), webpage_id=str(homepage.id))
    await queue(session, FINISH_TASK, run_id=str(run.id))


async def fetch_page(
    session: AsyncSession,
    http: httpx.AsyncClient,
    store: ObjectStore,
    *,
    run_id: uuid.UUID,
    webpage_id: uuid.UUID,
) -> Fetch:
    """GET the webpage and log the attempt as a `fetches` row. A 200 hands the body to
    `ingest.store`: `fetched` with the new snapshot, or `unchanged` when the bytes are the ones
    already kept. Any other status is `failed_http`, and a timeout `failed_timeout`."""
    webpage = await session.get_one(Webpage, webpage_id)
    fetch = Fetch(crawl_run_id=run_id, webpage_id=webpage.id, requested_at=utcnow())
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
        else:
            fetch.outcome = FetchOutcome.FAILED_HTTP
    session.add(fetch)
    await session.flush()
    return fetch


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
    "START_TASK",
    "ensure_domain",
    "ensure_webpage",
    "fetch_page",
    "finish_run",
    "get_run",
    "host_of",
    "media_type_of",
    "queue",
    "start_run",
]
