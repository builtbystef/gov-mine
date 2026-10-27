import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Path, Response

from gov_mine.dependencies import ObjectStoreDep, SessionDep
from gov_mine.modules.ingest import service

router = APIRouter(prefix="/snapshots", tags=["snapshots"])

_MARKDOWN: dict[int | str, dict[str, Any]] = {200: {"content": {"text/markdown": {}}}}
_BYTES: dict[int | str, dict[str, Any]] = {200: {"content": {"application/octet-stream": {}}}}


@router.get("/{snapshot_id}/text/{page}", response_class=Response, responses=_MARKDOWN)
async def read_text(
    snapshot_id: uuid.UUID,
    page: Annotated[int, Path(ge=1)],
    session: SessionDep,
    store: ObjectStoreDep,
) -> Response:
    """The markdown of one page of the snapshot, from 1. 409 while it is being parsed; 404 when
    it has no text."""
    markdown = await service.text(session, store, snapshot_id, page)
    return Response(markdown, media_type=service.TEXT_MEDIA_TYPE)


@router.get("/{snapshot_id}/bytes", response_class=Response, responses=_BYTES)
async def read_bytes(
    snapshot_id: uuid.UUID, session: SessionDep, store: ObjectStoreDep
) -> Response:
    """The snapshot's raw bytes, with the media type they were fetched with."""
    data, media_type = await service.raw_bytes(session, store, snapshot_id)
    return Response(data, media_type=media_type)
