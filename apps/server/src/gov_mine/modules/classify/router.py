import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from gov_mine.dependencies import SessionDep
from gov_mine.modules.classify import service
from gov_mine.modules.classify.models import Document
from gov_mine.modules.classify.schemas import (
    DocumentDetail,
    DocumentOutput,
    DocumentRef,
    DocumentTypeCount,
    DocumentVersion,
    SourceOutput,
)
from gov_mine.modules.institutions.models import DocumentType
from gov_mine.shared.pagination import Limit, Offset, Page

router = APIRouter(prefix="/runs", tags=["runs"])
documents_router = APIRouter(prefix="/documents", tags=["documents"])


def _document(document: Document, url: str) -> DocumentOutput:
    return DocumentOutput(
        id=document.id,
        webpage_id=document.webpage_id,
        url=url,
        document_type=document.document_type,
        title=document.title,
        document_date=document.document_date,
        created_at=document.created_at,
    )


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
    items = [_document(document, url) for document, url in rows]
    return Page(items=items, total=total, limit=limit, offset=offset)


@documents_router.get("")
async def list_documents(  # noqa: PLR0913, PLR0917 - the page and its three filters
    session: SessionDep,
    institution: uuid.UUID | None = None,
    document_type: Annotated[DocumentType | None, Query(alias="type")] = None,
    since: date | None = None,
    limit: Limit = 50,
    offset: Offset = 0,
) -> Page[DocumentOutput]:
    """Documents, newest dated first and undated last, by institution, type, or dated on or
    after `since`."""
    rows, total = await service.list_documents(
        session,
        institution_id=institution,
        document_type=document_type,
        since=since,
        limit=limit,
        offset=offset,
    )
    items = [_document(document, url) for document, url in rows]
    return Page(items=items, total=total, limit=limit, offset=offset)


@documents_router.get("/{document_id}")
async def read_document(document_id: uuid.UUID, session: SessionDep) -> DocumentDetail:
    """The document with its parent document, if any, and its versions: the webpage's snapshots
    with distinct text, newest first."""
    document, url, institution, parent, versions = await service.read_document(session, document_id)
    return DocumentDetail(
        **_document(document, url).model_dump(),
        institution_id=document.institution_id,
        institution_name=institution,
        parent=DocumentRef(id=parent.id, title=parent.title) if parent else None,
        versions=[
            DocumentVersion(
                snapshot_id=snapshot.id,
                text_hash=snapshot.text_hash,
                media_type=snapshot.media_type,
                created_at=snapshot.created_at,
            )
            for snapshot in versions
        ],
    )
