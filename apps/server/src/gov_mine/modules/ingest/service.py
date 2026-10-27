"""Snapshots: a webpage's bytes, kept once per distinct content, and the markdown parsed from
them. The bytes live in object storage at `bytes/<snapshot id>` and the markdown, one object per
page from 1, at `text/<snapshot id>/<page>`; the row says what they are."""

import asyncio
import hashlib
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.integrations import parser
from gov_mine.integrations.storage import ObjectNotFoundError, ObjectStore
from gov_mine.jobs import registry
from gov_mine.jobs.tasks import defer
from gov_mine.modules.ingest.models import TextStatus, WebpageSnapshot
from gov_mine.shared.exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)

PARSE_TASK = "ingest.parse"
TEXT_MEDIA_TYPE = "text/markdown; charset=utf-8"


class TextNotReady(ConflictError):  # noqa: N818 - the spec's name (section 8)
    """The snapshot is still being parsed."""


class NoText(NotFoundError):  # noqa: N818 - the spec's name (section 8)
    """The snapshot has no text: it is kept without (an image) or its parse failed."""


def bytes_key(snapshot_id: uuid.UUID) -> str:
    return f"bytes/{snapshot_id}"


def text_key(snapshot_id: uuid.UUID, page: int) -> str:
    return f"text/{snapshot_id}/{page}"


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def store(  # noqa: PLR0913 - the snapshot's four facts and what it works with
    session: AsyncSession,
    object_store: ObjectStore,
    webpage_id: uuid.UUID,
    data: bytes,
    media_type: str,
    *,
    run_id: uuid.UUID,
) -> uuid.UUID | None:
    """Keep `data` as a new snapshot of the webpage, queue its `ingest.parse` in the run, and
    return its id, or None when the webpage already has a snapshot with these bytes. The bytes
    are stored before the row is inserted: an object with no row is harmless, a row with no
    object is not."""
    digest = content_hash(data)
    kept = select(WebpageSnapshot.id).where(
        WebpageSnapshot.webpage_id == webpage_id, WebpageSnapshot.content_hash == digest
    )
    if await session.scalar(kept) is not None:
        return None
    snapshot_id = uuid.uuid7()
    await object_store.put(bytes_key(snapshot_id), data, media_type)
    # A concurrent fetch of the same bytes may have inserted the row meanwhile.
    stored = await session.scalar(
        insert(WebpageSnapshot)
        .values(
            id=snapshot_id,
            webpage_id=webpage_id,
            content_hash=digest,
            media_type=media_type,
            size_bytes=len(data),
        )
        .on_conflict_do_nothing()
        .returning(WebpageSnapshot.id)
    )
    if stored is not None:
        await defer(
            session, registry.tasks[PARSE_TASK], run_id=str(run_id), snapshot_id=str(stored)
        )
    return stored


async def get_snapshot(session: AsyncSession, snapshot_id: uuid.UUID) -> WebpageSnapshot:
    snapshot = await session.get(WebpageSnapshot, snapshot_id)
    if snapshot is None:
        raise NotFoundError(f"Snapshot {snapshot_id} not found")
    return snapshot


async def parse(session: AsyncSession, store: ObjectStore, snapshot_id: uuid.UUID) -> None:
    """Parse a `parsing` snapshot's bytes into `text/<id>/<page>` and mark it `ready`, `none` when
    its type is kept without text, or `failed` with the parser's message. A failure is the
    snapshot's state: its bytes stay, and it is not retried."""
    snapshot = await get_snapshot(session, snapshot_id)
    if snapshot.text_status is not TextStatus.PARSING:
        return
    data = await store.get(bytes_key(snapshot.id))
    try:
        parsed = await asyncio.to_thread(parser.parse, data, snapshot.media_type)
    except parser.ParseError as exc:
        logger.info("Snapshot %s did not parse: %s", snapshot.id, exc)
        snapshot.text_status, snapshot.text_error = TextStatus.FAILED, str(exc)
        return
    if parsed is None:
        snapshot.text_status = TextStatus.NONE
        return
    for page, markdown in enumerate(parsed.pages, start=1):
        await store.put(text_key(snapshot.id, page), markdown.encode(), TEXT_MEDIA_TYPE)
    snapshot.parser = parsed.parser
    snapshot.text_status = TextStatus.READY


async def text(session: AsyncSession, store: ObjectStore, snapshot_id: uuid.UUID, page: int) -> str:
    """The markdown of the snapshot's `page`, from 1. Raises `TextNotReady` while it is parsed,
    `NoText` when it has none, and `NotFoundError` for a page it does not have."""
    snapshot = await get_snapshot(session, snapshot_id)
    if snapshot.text_status is TextStatus.PARSING:
        raise TextNotReady(f"Snapshot {snapshot_id} is still being parsed")
    if snapshot.text_status in {TextStatus.NONE, TextStatus.FAILED}:
        raise NoText(f"Snapshot {snapshot_id} has no text ({snapshot.text_status})")
    try:
        return (await store.get(text_key(snapshot.id, page))).decode()
    except ObjectNotFoundError:
        raise NotFoundError(f"Snapshot {snapshot_id} has no page {page}") from None


async def raw_bytes(
    session: AsyncSession, store: ObjectStore, snapshot_id: uuid.UUID
) -> tuple[bytes, str]:
    """The snapshot's stored bytes and their media type."""
    snapshot = await get_snapshot(session, snapshot_id)
    return await store.get(bytes_key(snapshot.id)), snapshot.media_type


__all__ = [
    "PARSE_TASK",
    "NoText",
    "TextNotReady",
    "bytes_key",
    "content_hash",
    "get_snapshot",
    "parse",
    "raw_bytes",
    "store",
    "text",
    "text_key",
]
