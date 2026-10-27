"""Creating runs and reading them back with their fetch log."""

import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.db.base import utcnow
from gov_mine.modules.crawl import service as crawl
from gov_mine.modules.crawl.models import CrawlRun, Fetch, FetchOutcome, RunStatus, Webpage
from gov_mine.modules.extract import service as extract
from gov_mine.modules.ingest.models import WebpageSnapshot
from gov_mine.modules.institutions import service as institutions
from gov_mine.modules.institutions.models import Institution
from gov_mine.modules.ledger.models import AICall
from gov_mine.modules.runs.schemas import (
    FetchOutput,
    RunCounts,
    RunMode,
    RunOutput,
    RunSettings,
    RunTrigger,
    SnapshotSummary,
)
from gov_mine.shared.exceptions import ConflictError

ACTIVE_STATUSES = (RunStatus.QUEUED, RunStatus.RUNNING)


async def create_run(
    session: AsyncSession,
    institution_id: uuid.UUID,
    *,
    trigger: RunTrigger,
    mode: RunMode,
    limit: int | None = None,
) -> CrawlRun:
    """A `queued` run of the institution, and its `crawl.start` job in the same transaction.
    With `limit`, the run sends at most that many requests. Its settings record the fence's
    size cap. Raises `NotFoundError` for an unknown institution and `ConflictError` when it has
    a queued or running run, before anything is written."""
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
        ).model_dump(),
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


async def list_fetches(
    session: AsyncSession, run_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[FetchOutput], int]:
    """The run's fetch log in the order the requests were made. Raises `NotFoundError` for an
    unknown run."""
    await crawl.get_run(session, run_id)
    total = (
        await session.scalar(
            select(func.count()).select_from(Fetch).where(Fetch.crawl_run_id == run_id)
        )
        or 0
    )
    rows = await session.execute(
        select(Fetch, Webpage.url, WebpageSnapshot)
        .join(Webpage, Webpage.id == Fetch.webpage_id)
        .outerjoin(WebpageSnapshot, WebpageSnapshot.id == Fetch.snapshot_id)
        .where(Fetch.crawl_run_id == run_id)
        .order_by(Fetch.requested_at, Fetch.id)
        .limit(limit)
        .offset(offset)
    )
    items = [
        FetchOutput(
            id=fetch.id,
            webpage_id=fetch.webpage_id,
            url=url,
            requested_at=fetch.requested_at,
            duration_ms=fetch.duration_ms,
            outcome=fetch.outcome,
            http_status=fetch.http_status,
            reason=fetch.reason,
            snapshot=None
            if snapshot is None
            else SnapshotSummary(
                id=snapshot.id,
                content_hash=snapshot.content_hash,
                media_type=snapshot.media_type,
                size_bytes=snapshot.size_bytes,
            ),
        )
        for fetch, url, snapshot in rows
    ]
    return items, total


__all__ = ["create_run", "list_fetches", "list_runs", "read_run"]
