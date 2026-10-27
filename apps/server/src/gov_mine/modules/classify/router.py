import uuid

from fastapi import APIRouter

from gov_mine.dependencies import SessionDep
from gov_mine.modules.classify import service
from gov_mine.modules.classify.schemas import DocumentOutput, DocumentTypeCount, SourceOutput
from gov_mine.shared.pagination import Limit, Offset, Page

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}/sources")
async def list_run_sources(
    run_id: uuid.UUID, session: SessionDep, limit: Limit = 50, offset: Offset = 0
) -> Page[SourceOutput]:
    """The sources found by the run's classifications, next crawl first."""
    rows, total = await service.list_run_sources(session, run_id, limit=limit, offset=offset)
    items = [
        SourceOutput(
            id=source.id,
            webpage_id=source.webpage_id,
            url=url,
            document_type=source.document_type,
            crawl_interval=source.crawl_interval,
            next_crawl_at=source.next_crawl_at,
        )
        for source, url in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{run_id}/document-counts")
async def count_run_documents(run_id: uuid.UUID, session: SessionDep) -> list[DocumentTypeCount]:
    """How many documents the run's classifications found, by type."""
    counts = await service.count_run_documents(session, run_id)
    return [DocumentTypeCount(document_type=kind, count=count) for kind, count in counts.items()]


@router.get("/{run_id}/documents")
async def list_run_documents(
    run_id: uuid.UUID, session: SessionDep, limit: Limit = 50, offset: Offset = 0
) -> Page[DocumentOutput]:
    """The documents the run created or gave a new version, by type then title."""
    rows, total = await service.list_run_documents(session, run_id, limit=limit, offset=offset)
    items = [
        DocumentOutput(
            id=document.id,
            webpage_id=document.webpage_id,
            url=url,
            document_type=document.document_type,
            title=document.title,
            document_date=document.document_date,
            created_at=document.created_at,
        )
        for document, url in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)
