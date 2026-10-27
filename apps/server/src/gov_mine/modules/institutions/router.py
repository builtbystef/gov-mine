import uuid

from fastapi import APIRouter, status

from gov_mine.dependencies import SessionDep
from gov_mine.modules.institutions import service
from gov_mine.modules.institutions.schemas import InstitutionInput, InstitutionOutput
from gov_mine.shared.pagination import Limit, Offset, Page

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("")
async def list_institutions(
    session: SessionDep, limit: Limit = 50, offset: Offset = 0
) -> Page[InstitutionOutput]:
    """Every institution, by name, with its last run and when the next is due."""
    items, total = await service.list_institutions(session, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_institution(data: InstitutionInput, session: SessionDep) -> InstitutionOutput:
    """Adds the institution and makes its website's host a `crawl` domain."""
    institution = await service.create_institution(session, data)
    await session.commit()
    return await service.read_institution(session, institution.id)


@router.get("/{institution_id}")
async def read_institution(institution_id: uuid.UUID, session: SessionDep) -> InstitutionOutput:
    return await service.read_institution(session, institution_id)


@router.put("/{institution_id}")
async def update_institution(
    institution_id: uuid.UUID, data: InstitutionInput, session: SessionDep
) -> InstitutionOutput:
    """Replaces the institution's fields; its website's host becomes a `crawl` domain."""
    await service.update_institution(session, institution_id, data)
    await session.commit()
    return await service.read_institution(session, institution_id)
