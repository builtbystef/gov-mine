import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from gov_mine.dependencies import SessionDep
from gov_mine.modules.crawl.models import FetchOutcome
from gov_mine.modules.runs import service
from gov_mine.modules.runs.schemas import (
    FetchOutput,
    RunCreate,
    RunOutput,
    RunReport,
    SnapshotOutput,
    WebpageOutput,
)
from gov_mine.shared.pagination import Limit, Offset, Page

router = APIRouter(prefix="/runs", tags=["runs"])
snapshots_router = APIRouter(prefix="/snapshots", tags=["snapshots"])
webpages_router = APIRouter(prefix="/webpages", tags=["webpages"])


@router.get("")
async def list_runs(session: SessionDep, limit: Limit = 50, offset: Offset = 0) -> Page[RunOutput]:
    """Every run, newest first."""
    items, total = await service.list_runs(session, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_run(data: RunCreate, session: SessionDep) -> RunOutput:
    """Queues a full run of the institution from the dashboard. 409 while it has a queued or
    running run."""
    run = await service.create_run(
        session, data.institution_id, trigger="dashboard", mode=data.mode
    )
    await session.commit()
    return await service.read_run(session, run.id)


@router.get("/{run_id}")
async def read_run(run_id: uuid.UUID, session: SessionDep) -> RunOutput:
    return await service.read_run(session, run_id)


@router.get("/{run_id}/report")
async def read_report(run_id: uuid.UUID, session: SessionDep) -> RunReport:
    """The run's numbers, each a query over its logs. Costs come from `ai_calls`: estimated from
    the price list, and as reported by OpenRouter."""
    return await service.report(session, run_id)


@router.get("/{run_id}/fetches")
async def list_fetches(  # noqa: PLR0913, PLR0917 - the page and its two filters
    run_id: uuid.UUID,
    session: SessionDep,
    limit: Limit = 50,
    offset: Offset = 0,
    outcome: FetchOutcome | None = None,
    q: Annotated[str | None, Query(max_length=2048)] = None,
) -> Page[FetchOutput]:
    """The run's fetch log, one row per attempt, in the order the requests were made: only those
    with `outcome`, and only URLs containing `q` (any case), when given."""
    items, total = await service.list_fetches(
        session, run_id, limit=limit, offset=offset, outcome=outcome, q=q
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{run_id}/snapshots")
async def list_snapshots(
    run_id: uuid.UUID, session: SessionDep, limit: Limit = 50, offset: Offset = 0
) -> Page[SnapshotOutput]:
    """The snapshots the run wrote, in the order it wrote them."""
    items, total = await service.list_snapshots(session, run_id, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@snapshots_router.get("/{snapshot_id}")
async def read_snapshot(snapshot_id: uuid.UUID, session: SessionDep) -> SnapshotOutput:
    return await service.read_snapshot(session, snapshot_id)


@webpages_router.get("/{webpage_id}")
async def read_webpage(webpage_id: uuid.UUID, session: SessionDep) -> WebpageOutput:
    """The webpage, its domain, `missing_since`, every fetch of it newest first, and its
    snapshots newest first."""
    return await service.read_webpage(session, webpage_id)
