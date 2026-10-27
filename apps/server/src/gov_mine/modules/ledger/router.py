import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from gov_mine.dependencies import SessionDep
from gov_mine.modules.ledger import service
from gov_mine.modules.ledger.schemas import AICallOutput
from gov_mine.shared.pagination import Limit, Offset, Page

router = APIRouter(prefix="/ai-calls", tags=["ai-calls"])


@router.get("")
async def list_ai_calls(
    session: SessionDep,
    run: Annotated[uuid.UUID, Query()],
    limit: Limit = 50,
    offset: Offset = 0,
) -> Page[AICallOutput]:
    """The run's paid calls, by purpose, oldest first within each."""
    calls, total = await service.list_calls(session, run, limit=limit, offset=offset)
    items = [AICallOutput.model_validate(call, from_attributes=True) for call in calls]
    return Page(items=items, total=total, limit=limit, offset=offset)
