import uuid
from typing import TYPE_CHECKING

import pytest

from gov_mine.modules.crawl.models import CrawlPolicy, Domain, Webpage
from gov_mine.modules.ingest import service as ingest
from gov_mine.modules.ingest.models import TextStatus, WebpageSnapshot

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from tests.integration.conftest import Database

    from gov_mine.integrations.storage.memory import MemoryObjectStore

HTML = b"<html><body><nav>Menu</nav><main><h1>Parkdale Hub</h1><p>Body.</p></main></body></html>"


async def _store_page(db: Database, store: MemoryObjectStore) -> uuid.UUID:
    async with db.session() as session:
        domain = Domain(name="createto.ca", crawl_policy=CrawlPolicy.CRAWL)
        session.add(domain)
        await session.flush()
        page = Webpage(url="https://createto.ca/", domain_id=domain.id)
        session.add(page)
        await session.flush()
        snapshot_id = await ingest.store(
            session, store, page.id, HTML, "text/html", run_id=uuid.uuid7()
        )
        await session.commit()
        assert snapshot_id is not None
        return snapshot_id


async def _text_with_status(
    db: Database, store: MemoryObjectStore, snapshot_id: uuid.UUID, status: TextStatus
) -> str:
    async with db.session() as session:
        snapshot = await session.get_one(WebpageSnapshot, snapshot_id)
        snapshot.text_status = status
        await session.flush()
        return await ingest.text(session, store, snapshot_id, 1)


def test_the_snapshot_text_and_bytes_are_served(
    client: TestClient, db: Database, object_store: MemoryObjectStore
):
    snapshot_id = db.run(_store_page, db, object_store)

    text = client.get(f"/snapshots/{snapshot_id}/text/1")
    raw = client.get(f"/snapshots/{snapshot_id}/bytes")

    assert text.status_code == 200
    assert text.text == "# Parkdale Hub\n\nBody.\n"
    assert text.headers["content-type"].startswith("text/markdown")
    assert raw.status_code == 200
    assert raw.content == HTML
    assert raw.headers["content-type"].startswith("text/html")
    assert db.run(_text_with_status, db, object_store, snapshot_id, TextStatus.READY) == text.text
    with pytest.raises(ingest.TextNotReady):
        db.run(_text_with_status, db, object_store, snapshot_id, TextStatus.PARSING)
    for status in (TextStatus.NONE, TextStatus.FAILED):
        with pytest.raises(ingest.NoText):
            db.run(_text_with_status, db, object_store, snapshot_id, status)
