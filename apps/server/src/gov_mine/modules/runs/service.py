"""Creating runs and reading them back with their fetch log."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.modules.crawl import service as crawl
from gov_mine.modules.crawl.models import CrawlRun, Fetch, RunStatus, Webpage
from gov_mine.modules.ingest.models import WebpageSnapshot
from gov_mine.modules.institutions import service as institutions
from gov_mine.modules.institutions.models import Institution
from gov_mine.modules.runs.schemas import (
    FetchOutput,
    RunMode,
    RunOutput,
    RunSettings,
    RunTrigger,
    SnapshotSummary,
)


async def create_run(
    session: AsyncSession,
    institution_id: uuid.UUID,
    *,
    trigger: RunTrigger,
    mode: RunMode,
    limit: int | None = None,
) -> CrawlRun:
    """A `queued` run of the institution, and its `crawl.start` job in the same transaction.
    With `limit`, the run sends at most that many requests. Raises `NotFoundError` for an
    unknown institution, before anything is written."""
    await institutions.get_institution(session, institution_id)
    run = CrawlRun(
        institution_id=institution_id,
        status=RunStatus.QUEUED,
        settings=RunSettings(trigger=trigger, mode=mode, limit=limit).model_dump(),
    )
    session.add(run)
    await session.flush()
    await crawl.queue(session, crawl.START_TASK, run_id=str(run.id))
    return run


def _run_output(run: CrawlRun, institution_name: str) -> RunOutput:
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
    )


_RUNS = select(CrawlRun, Institution.name).join(
    Institution, Institution.id == CrawlRun.institution_id
)


async def list_runs(
    session: AsyncSession, *, limit: int, offset: int
) -> tuple[list[RunOutput], int]:
    """Newest first."""
    total = await session.scalar(select(func.count()).select_from(CrawlRun)) or 0
    rows = await session.execute(
        _RUNS.order_by(CrawlRun.created_at.desc(), CrawlRun.id.desc()).limit(limit).offset(offset)
    )
    return [_run_output(run, name) for run, name in rows], total


async def read_run(session: AsyncSession, run_id: uuid.UUID) -> RunOutput:
    run = await crawl.get_run(session, run_id)
    institution = await session.get_one(Institution, run.institution_id)
    return _run_output(run, institution.name)


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
