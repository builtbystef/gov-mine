import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from gov_mine.dependencies import SessionDep
from gov_mine.modules.extract import service
from gov_mine.modules.extract.models import RecordType
from gov_mine.modules.extract.schemas import RecordDetail, RecordSummary, RecordTypeOutput
from gov_mine.shared.pagination import Limit, Offset, Page

router = APIRouter(tags=["records"])


@router.get("/record-types")
async def list_record_types() -> list[RecordTypeOutput]:
    """Every record type with its fields."""
    return [
        RecordTypeOutput(record_type=RecordType(name), fields=fields)
        for name, fields in service.record_fields().items()
    ]


@router.get("/records")
async def list_records(  # noqa: PLR0913, PLR0917 - the page and its three filters
    session: SessionDep,
    record_type: Annotated[RecordType | None, Query(alias="type")] = None,
    document: uuid.UUID | None = None,
    run: uuid.UUID | None = None,
    limit: Limit = 50,
    offset: Offset = 0,
) -> Page[RecordSummary]:
    """Current records, most recently extracted first, by type, by document, or those a run
    created or amended (then by type first)."""
    items, total = await service.list_records(
        session,
        record_type=record_type,
        document_id=document,
        run_id=run,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/records/{record_id}")
async def read_record(record_id: uuid.UUID, session: SessionDep) -> RecordDetail:
    """The record's current fields with their citations, and its record snapshots, newest
    first, each as the fields that changed."""
    return await service.read_record(session, record_id)
