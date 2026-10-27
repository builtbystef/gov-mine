"""Snapshots: a webpage's bytes, kept once per distinct content. The bytes live in object
storage at `bytes/<snapshot id>`; the row says what they are."""

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.integrations.storage import ObjectStore
from gov_mine.modules.ingest.models import WebpageSnapshot


def bytes_key(snapshot_id: uuid.UUID) -> str:
    return f"bytes/{snapshot_id}"


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def store(
    session: AsyncSession,
    object_store: ObjectStore,
    webpage_id: uuid.UUID,
    data: bytes,
    media_type: str,
) -> uuid.UUID | None:
    """Keep `data` as a new snapshot of the webpage and return its id, or None when the webpage
    already has a snapshot with these bytes. The bytes are stored before the row is inserted:
    an object with no row is harmless, a row with no object is not."""
    digest = content_hash(data)
    kept = select(WebpageSnapshot.id).where(
        WebpageSnapshot.webpage_id == webpage_id, WebpageSnapshot.content_hash == digest
    )
    if await session.scalar(kept) is not None:
        return None
    snapshot_id = uuid.uuid7()
    await object_store.put(bytes_key(snapshot_id), data, media_type)
    # A concurrent fetch of the same bytes may have inserted the row meanwhile.
    return await session.scalar(
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


__all__ = ["bytes_key", "content_hash", "store"]
