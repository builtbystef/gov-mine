"""Creating runs and reading them back with their fetch log."""

import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.db.base import utcnow
from gov_mine.modules.classify.models import Classification, Document
from gov_mine.modules.crawl import service as crawl
from gov_mine.modules.crawl.models import (
    CrawlRun,
    Domain,
    Fetch,
    FetchOutcome,
    RunStatus,
    Webpage,
)
from gov_mine.modules.extract import service as extract
from gov_mine.modules.ingest import service as ingest
from gov_mine.modules.ingest.models import TextStatus, WebpageSnapshot
from gov_mine.modules.institutions import service as institutions
from gov_mine.modules.institutions.models import Institution
from gov_mine.modules.ledger.models import AICall
from gov_mine.modules.runs.schemas import (
    FetchOutput,
    OutcomeCount,
    ProviderCost,
    PurposeCalls,
    RecordCounts,
    RemovedDocument,
    RunCounts,
    RunMode,
    RunOutput,
    RunReport,
    RunSettings,
    RunTrigger,
    SnapshotOutput,
    SnapshotSummary,
    WebpageOutput,
)
from gov_mine.shared.exceptions import ConflictError, NotFoundError

ACTIVE_STATUSES = (RunStatus.QUEUED, RunStatus.RUNNING)


async def create_run(  # noqa: PLR0913 - the run's settings, as keywords
    session: AsyncSession,
    institution_id: uuid.UUID,
    *,
    trigger: RunTrigger,
    mode: RunMode,
    limit: int | None = None,
    replay: str | None = None,
) -> CrawlRun:
    """A `queued` run of the institution, and its `crawl.start` job in the same transaction.
    With `limit`, the run sends at most that many requests. Its settings record the fence's
    size cap, and, on a replay run, the replay server's address `replay`. Raises
    `NotFoundError` for an unknown institution and `ConflictError` when it has a queued or
    running run, before anything is written."""
    await institutions.get_institution(session, institution_id)
    active = await session.scalar(
        select(CrawlRun.id).where(
            CrawlRun.institution_id == institution_id, CrawlRun.status.in_(ACTIVE_STATUSES)
        )
    )
    if active is not None:
        raise ConflictError(f"The institution already has an active run, {active}")
    run = CrawlRun(
        institution_id=institution_id,
        status=RunStatus.QUEUED,
        settings=RunSettings(
            trigger=trigger,
            mode=mode,
            limit=limit,
            max_file_bytes=crawl.MAX_FILE_BYTES,
            extractors=extract.extractor_versions(),
            replay=replay,
            cutoff=extract.window_cutoff(utcnow().date()),
        ).model_dump(mode="json"),
    )
    session.add(run)
    await session.flush()
    await crawl.queue(session, crawl.START_TASK, run_id=str(run.id))
    return run


_BUCKETS = {
    FetchOutcome.FETCHED: "fetched",
    FetchOutcome.NOT_MODIFIED: "not_modified",
    FetchOutcome.UNCHANGED: "not_modified",
    FetchOutcome.BLOCKED_ROBOTS: "blocked",
    FetchOutcome.SKIPPED_SCOPE: "skipped",
    FetchOutcome.SKIPPED_TYPE: "skipped",
    FetchOutcome.SKIPPED_SIZE: "skipped",
    FetchOutcome.SKIPPED_DEPTH: "skipped",
    FetchOutcome.FAILED_HTTP: "failed",
    FetchOutcome.FAILED_TIMEOUT: "failed",
}


async def _counts(session: AsyncSession, run_ids: list[uuid.UUID]) -> dict[uuid.UUID, RunCounts]:
    """Each run's fetches by outcome, snapshots written and model cost, in two grouped queries."""
    tallies: dict[uuid.UUID, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    rows = await session.execute(
        select(
            Fetch.crawl_run_id,
            Fetch.outcome,
            func.count(),
            func.count(case((Fetch.snapshot_id.is_not(None), 1))),
        )
        .where(Fetch.crawl_run_id.in_(run_ids))
        .group_by(Fetch.crawl_run_id, Fetch.outcome)
    )
    for run_id, outcome, count, snapshots in rows:
        tallies[run_id][_BUCKETS[FetchOutcome(outcome)]] += count
        tallies[run_id]["snapshots"] += snapshots
    costs = dict(
        (
            await session.execute(
                select(AICall.crawl_run_id, func.sum(AICall.cost))
                .where(AICall.crawl_run_id.in_(run_ids))
                .group_by(AICall.crawl_run_id)
            )
        ).all()
    )
    return {
        run_id: RunCounts(
            fetched=tallies[run_id]["fetched"],
            not_modified=tallies[run_id]["not_modified"],
            skipped=tallies[run_id]["skipped"],
            blocked=tallies[run_id]["blocked"],
            failed=tallies[run_id]["failed"],
            snapshots=tallies[run_id]["snapshots"],
            cost=costs.get(run_id) or Decimal(0),
        )
        for run_id in run_ids
    }


def _elapsed(run: CrawlRun) -> float | None:
    if run.started_at is None:
        return None
    return ((run.finished_at or utcnow()) - run.started_at).total_seconds()


def _run_output(run: CrawlRun, institution_name: str, counts: RunCounts) -> RunOutput:
    return RunOutput(
        id=run.id,
        institution_id=run.institution_id,
        institution_name=institution_name,
        status=run.status,
        settings=RunSettings.model_validate(run.settings),
        started_at=run.started_at,
        finished_at=run.finished_at,
        error=run.error,
        created_at=run.created_at,
        elapsed_seconds=_elapsed(run),
        counts=counts,
    )


_RUNS = select(CrawlRun, Institution.name).join(
    Institution, Institution.id == CrawlRun.institution_id
)


async def list_runs(
    session: AsyncSession, *, limit: int, offset: int
) -> tuple[list[RunOutput], int]:
    """Newest first."""
    total = await session.scalar(select(func.count()).select_from(CrawlRun)) or 0
    rows = (
        await session.execute(
            _RUNS.order_by(CrawlRun.created_at.desc(), CrawlRun.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    counts = await _counts(session, [run.id for run, _ in rows])
    return [_run_output(run, name, counts[run.id]) for run, name in rows], total


async def read_run(session: AsyncSession, run_id: uuid.UUID) -> RunOutput:
    run = await crawl.get_run(session, run_id)
    institution = await session.get_one(Institution, run.institution_id)
    counts = await _counts(session, [run.id])
    return _run_output(run, institution.name, counts[run.id])


def _snapshot_summary(snapshot: WebpageSnapshot | None) -> SnapshotSummary | None:
    if snapshot is None:
        return None
    return SnapshotSummary(
        id=snapshot.id,
        content_hash=snapshot.content_hash,
        media_type=snapshot.media_type,
        size_bytes=snapshot.size_bytes,
    )


def _fetch_output(fetch: Fetch, url: str, snapshot: WebpageSnapshot | None) -> FetchOutput:
    return FetchOutput(
        id=fetch.id,
        crawl_run_id=fetch.crawl_run_id,
        webpage_id=fetch.webpage_id,
        url=url,
        requested_at=fetch.requested_at,
        duration_ms=fetch.duration_ms,
        outcome=fetch.outcome,
        http_status=fetch.http_status,
        reason=fetch.reason,
        snapshot=_snapshot_summary(snapshot),
    )


async def list_fetches(  # noqa: PLR0913 - the page and its two filters, as keywords
    session: AsyncSession,
    run_id: uuid.UUID,
    *,
    limit: int,
    offset: int,
    outcome: FetchOutcome | None = None,
    q: str | None = None,
) -> tuple[list[FetchOutput], int]:
    """The run's fetch log in the order the requests were made, of one `outcome` and with `q` in
    the URL when given. Raises `NotFoundError` for an unknown run."""
    await crawl.get_run(session, run_id)
    where = [Fetch.crawl_run_id == run_id]
    if outcome is not None:
        where.append(Fetch.outcome == outcome)
    if q:
        where.append(Webpage.url.icontains(q, autoescape=True))
    total = (
        await session.scalar(
            select(func.count())
            .select_from(Fetch)
            .join(Webpage, Webpage.id == Fetch.webpage_id)
            .where(*where)
        )
        or 0
    )
    rows = await session.execute(
        select(Fetch, Webpage.url, WebpageSnapshot)
        .join(Webpage, Webpage.id == Fetch.webpage_id)
        .outerjoin(WebpageSnapshot, WebpageSnapshot.id == Fetch.snapshot_id)
        .where(*where)
        .order_by(Fetch.requested_at, Fetch.id)
        .limit(limit)
        .offset(offset)
    )
    return [_fetch_output(fetch, url, snapshot) for fetch, url, snapshot in rows], total


def _snapshot_output(snapshot: WebpageSnapshot, url: str) -> SnapshotOutput:
    return SnapshotOutput(
        id=snapshot.id,
        webpage_id=snapshot.webpage_id,
        url=url,
        content_hash=snapshot.content_hash,
        media_type=snapshot.media_type,
        size_bytes=snapshot.size_bytes,
        text_status=snapshot.text_status,
        text_error=snapshot.text_error,
        parser=snapshot.parser,
        stated_date=snapshot.stated_date,
        created_at=snapshot.created_at,
    )


async def list_snapshots(
    session: AsyncSession, run_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[SnapshotOutput], int]:
    """The snapshots the run's fetches wrote, in the order they were written. Raises
    `NotFoundError` for an unknown run."""
    await crawl.get_run(session, run_id)
    written = select(Fetch.snapshot_id).where(
        Fetch.crawl_run_id == run_id, Fetch.snapshot_id.is_not(None)
    )
    where = WebpageSnapshot.id.in_(written)
    total = await session.scalar(select(func.count()).select_from(WebpageSnapshot).where(where))
    rows = await session.execute(
        select(WebpageSnapshot, Webpage.url)
        .join(Webpage, Webpage.id == WebpageSnapshot.webpage_id)
        .where(where)
        .order_by(WebpageSnapshot.created_at, WebpageSnapshot.id)
        .limit(limit)
        .offset(offset)
    )
    return [_snapshot_output(snapshot, url) for snapshot, url in rows], total or 0


async def read_snapshot(session: AsyncSession, snapshot_id: uuid.UUID) -> SnapshotOutput:
    """Raises `NotFoundError` for an unknown snapshot."""
    snapshot = await ingest.get_snapshot(session, snapshot_id)
    webpage = await session.get_one(Webpage, snapshot.webpage_id)
    return _snapshot_output(snapshot, webpage.url)


async def read_webpage(session: AsyncSession, webpage_id: uuid.UUID) -> WebpageOutput:
    """A webpage with every fetch of it, newest first, and its snapshots. Raises `NotFoundError`
    for an unknown webpage."""
    webpage = await session.get(Webpage, webpage_id)
    if webpage is None:
        raise NotFoundError(f"Webpage {webpage_id} not found")
    domain = await session.get_one(Domain, webpage.domain_id)
    fetches = await session.execute(
        select(Fetch, WebpageSnapshot)
        .outerjoin(WebpageSnapshot, WebpageSnapshot.id == Fetch.snapshot_id)
        .where(Fetch.webpage_id == webpage_id)
        .order_by(Fetch.requested_at.desc(), Fetch.id.desc())
    )
    snapshots = await session.scalars(
        select(WebpageSnapshot)
        .where(WebpageSnapshot.webpage_id == webpage_id)
        .order_by(WebpageSnapshot.created_at.desc(), WebpageSnapshot.id.desc())
    )
    return WebpageOutput(
        id=webpage.id,
        url=webpage.url,
        domain=domain.name,
        missing_since=webpage.missing_since,
        fetches=[_fetch_output(fetch, webpage.url, snapshot) for fetch, snapshot in fetches],
        snapshots=[_snapshot_output(snapshot, webpage.url) for snapshot in snapshots],
    )


async def _records(_session: AsyncSession, _run_id: uuid.UUID) -> RecordCounts | None:
    """Records created and amended in the run. TODO(023): wire up once `records` and
    `record_snapshots` exist: created = records whose first record snapshot's extraction has
    this `crawl_run_id`, amended = record snapshots of the run's extractions that are not
    their record's first. Null until then, which the report prints as not available."""
    return None


async def _unextracted(_session: AsyncSession, _run_id: uuid.UUID) -> list[uuid.UUID] | None:
    """Documents left unextracted because their extraction in the run failed. TODO(023): the
    documents whose webpage snapshot has an `extractions` row of this run with `error` set."""
    return None


async def _fallback_reasons(
    _session: AsyncSession, _run_id: uuid.UUID
) -> dict[str, dict[str, int]] | None:
    """`fallback_reason` counts per source. TODO(023): the run's `extractions` with
    `fallback_reason` set, grouped by their document's `source_id` and the reason."""
    return None


async def report(session: AsyncSession, run_id: uuid.UUID) -> RunReport:
    """The run's numbers, every one a query over the logs. Raises `NotFoundError` for an
    unknown run."""
    run = await read_run(session, run_id)
    in_run = Fetch.crawl_run_id == run_id
    sent = Fetch.duration_ms.is_not(None)

    outcomes = [
        OutcomeCount(outcome=outcome, fetches=fetches, requests=requests)
        for outcome, fetches, requests in await session.execute(
            select(Fetch.outcome, func.count(), func.count().filter(sent))
            .where(in_run)
            .group_by(Fetch.outcome)
            .order_by(Fetch.outcome)
        )
    ]

    written = select(Fetch.snapshot_id).where(in_run, Fetch.snapshot_id.is_not(None))
    status_counts = dict(
        (
            await session.execute(
                select(WebpageSnapshot.text_status, func.count())
                .where(WebpageSnapshot.id.in_(written))
                .group_by(WebpageSnapshot.text_status)
            )
        ).all()
    )
    parsing = status_counts.get(TextStatus.PARSING, 0)

    classified_in_run = (
        select(WebpageSnapshot.webpage_id)
        .join(Classification, Classification.snapshot_id == WebpageSnapshot.id)
        .where(Classification.crawl_run_id == run_id)
    )
    changed_in_run = select(WebpageSnapshot.webpage_id).where(WebpageSnapshot.id.in_(written))
    documents_new = await session.scalar(
        select(func.count()).select_from(Document).where(Document.webpage_id.in_(classified_in_run))
    )
    documents_changed = await session.scalar(
        select(func.count())
        .select_from(Document)
        .where(
            Document.webpage_id.in_(changed_in_run),
            Document.webpage_id.not_in(classified_in_run),
        )
    )

    by_purpose = [
        PurposeCalls(
            purpose=purpose,
            calls=calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost,
            reported_cost=reported,
        )
        for purpose, calls, input_tokens, output_tokens, cost, reported in await session.execute(
            select(
                AICall.purpose,
                func.count(),
                func.sum(AICall.input_tokens),
                func.sum(AICall.output_tokens),
                func.sum(AICall.cost),
                func.sum(AICall.reported_cost),
            )
            .where(AICall.crawl_run_id == run_id)
            .group_by(AICall.purpose)
            .order_by(AICall.purpose)
        )
    ]
    by_provider = [
        ProviderCost(
            provider=provider,
            calls=calls,
            estimated_cost=cost,
            reported_cost=reported,
            calls_without_reported_cost=unreported,
        )
        for provider, calls, cost, reported, unreported in await session.execute(
            select(
                AICall.provider,
                func.count(),
                func.sum(AICall.cost),
                func.sum(AICall.reported_cost),
                func.count().filter(AICall.reported_cost.is_(None)),
            )
            .where(AICall.crawl_run_id == run_id)
            .group_by(AICall.provider)
            .order_by(AICall.provider)
        )
    ]

    # `missing_since` is the requested_at of the first 404, so equal to one of the run's fetches
    # only when the page went missing in this run.
    removed = [
        RemovedDocument(document_id=document_id, url=url, title=title, missing_since=since)
        for document_id, url, title, since in await session.execute(
            select(Document.id, Webpage.url, Document.title, Fetch.requested_at)
            .join(Webpage, Webpage.id == Document.webpage_id)
            .join(
                Fetch,
                (Fetch.webpage_id == Webpage.id)
                & in_run
                & (Fetch.requested_at == Webpage.missing_since),
            )
            .order_by(Webpage.url)
        )
    ]

    elapsed = (
        (run.finished_at - run.started_at).total_seconds()
        if run.started_at is not None and run.finished_at is not None
        else None
    )
    return RunReport(
        run=run,
        elapsed_seconds=elapsed,
        requests_sent=sum(count.requests for count in outcomes),
        fetches_by_outcome=outcomes,
        snapshots_written=sum(status_counts.values()),
        files_processed=sum(status_counts.values()) - parsing,
        files_failed=status_counts.get(TextStatus.FAILED, 0),
        files_parsing=parsing,
        documents_new=documents_new or 0,
        documents_changed=documents_changed or 0,
        records=await _records(session, run_id),
        paid_calls=sum(purpose.calls for purpose in by_purpose),
        estimated_cost=sum((purpose.estimated_cost for purpose in by_purpose), Decimal(0)),
        reported_cost=await session.scalar(
            select(func.sum(AICall.reported_cost)).where(AICall.crawl_run_id == run_id)
        ),
        calls_by_purpose=by_purpose,
        cost_by_provider=by_provider,
        removed_documents=removed,
        unextracted_document_ids=await _unextracted(session, run_id),
        fallback_reasons_by_source=await _fallback_reasons(session, run_id),
    )


_NOT_AVAILABLE = "not available (no extraction yet)"


def _usd(amount: Decimal | None) -> str:
    return "none reported" if amount is None else f"${amount:.6f}"


def report_markdown(report: RunReport) -> str:
    """The report as markdown tables, for the README and the terminal."""
    run = report.run
    elapsed = (
        "not finished" if report.elapsed_seconds is None else f"{report.elapsed_seconds:.1f} s"
    )
    records = (
        (_NOT_AVAILABLE, _NOT_AVAILABLE)
        if report.records is None
        else (str(report.records.created), str(report.records.amended))
    )
    rows = [
        ("Run", f"{run.id} ({run.institution_name}, {run.settings.mode}, {run.status})"),
        ("Time taken", elapsed),
        ("Requests sent", str(report.requests_sent)),
        ("Snapshots written", str(report.snapshots_written)),
        ("Files processed", str(report.files_processed)),
        ("Files failed", str(report.files_failed)),
        ("Files still parsing", str(report.files_parsing)),
        ("Documents new", str(report.documents_new)),
        ("Documents changed", str(report.documents_changed)),
        ("Documents removed", str(len(report.removed_documents))),
        ("Records created", records[0]),
        ("Records amended", records[1]),
        ("Paid calls", str(report.paid_calls)),
        ("Cost, estimated from the price list", _usd(report.estimated_cost)),
        ("Cost, reported by OpenRouter", _usd(report.reported_cost)),
    ]
    lines = ["| Number | Value |", "| --- | --- |", *(f"| {k} | {v} |" for k, v in rows)]

    lines += ["", "| Fetch outcome | Fetches | Requests sent |", "| --- | ---: | ---: |"]
    lines += [f"| {o.outcome} | {o.fetches} | {o.requests} |" for o in report.fetches_by_outcome]

    lines += [
        "",
        (
            "| Paid calls by purpose | Calls | Input tokens | Output tokens"
            " | Estimated (price list) | Reported (OpenRouter) |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines += [
        f"| {p.purpose} | {p.calls} | {p.input_tokens} | {p.output_tokens}"
        f" | {_usd(p.estimated_cost)} | {_usd(p.reported_cost)} |"
        for p in report.calls_by_purpose
    ]

    lines += [
        "",
        (
            "| Cost by provider | Calls | Estimated (price list) | Reported (OpenRouter)"
            " | Calls with no reported cost |"
        ),
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    lines += [
        f"| {p.provider} | {p.calls} | {_usd(p.estimated_cost)} | {_usd(p.reported_cost)}"
        f" | {p.calls_without_reported_cost} |"
        for p in report.cost_by_provider
    ]

    lines += ["", "Removed documents (webpage went missing in this run):"]
    lines += [f"- {d.url} ({d.title or 'untitled'})" for d in report.removed_documents] or [
        "- none"
    ]
    lines += ["", "Unextracted documents (extraction failed):"]
    if report.unextracted_document_ids is None:
        lines.append(f"- {_NOT_AVAILABLE}")
    else:
        lines += [f"- {i}" for i in report.unextracted_document_ids] or ["- none"]
    lines += ["", "Fallback reasons per source:"]
    if report.fallback_reasons_by_source is None:
        lines.append(f"- {_NOT_AVAILABLE}")
    else:
        lines += [
            f"- {source}: {reason} {count}"
            for source, reasons in report.fallback_reasons_by_source.items()
            for reason, count in reasons.items()
        ] or ["- none"]
    return "\n".join(lines)


__all__ = ["create_run", "list_fetches", "list_runs", "read_run", "report", "report_markdown"]
