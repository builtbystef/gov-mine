import uuid

from fastapi import APIRouter

from gov_mine.dependencies import SessionDep
from gov_mine.modules.runs import service
from gov_mine.modules.runs.schemas import FetchOutput, RunOutput
from gov_mine.shared.pagination import Limit, Offset, Page

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("")
async def list_runs(session: SessionDep, limit: Limit = 50, offset: Offset = 0) -> Page[RunOutput]:
    """Every run, newest first."""
    items, total = await service.list_runs(session, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{run_id}")
async def read_run(run_id: uuid.UUID, session: SessionDep) -> RunOutput:
    return await service.read_run(session, run_id)


@router.get("/{run_id}/fetches")
async def list_fetches(
    run_id: uuid.UUID, session: SessionDep, limit: Limit = 50, offset: Offset = 0
) -> Page[FetchOutput]:
    """The run's fetch log, one row per attempt, in the order the requests were made."""
    items, total = await service.list_fetches(session, run_id, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)
