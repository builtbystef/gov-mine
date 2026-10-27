import hashlib
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select

from gov_mine.modules.crawl.models import CrawlPolicy, Domain, Webpage
from gov_mine.modules.ingest import service as ingest
from gov_mine.modules.ingest.models import TextStatus, WebpageSnapshot

if TYPE_CHECKING:
    from tests.integration.conftest import Database

    from gov_mine.integrations.storage.memory import MemoryObjectStore


async def _store_three_versions(
    db: Database, store: MemoryObjectStore
) -> tuple[uuid.UUID | None, uuid.UUID | None, uuid.UUID | None, list[WebpageSnapshot]]:
    async with db.session() as session:
        domain = Domain(name="createto.ca", crawl_policy=CrawlPolicy.CRAWL)
        session.add(domain)
        await session.flush()
        page = Webpage(url="https://createto.ca/", domain_id=domain.id)
        session.add(page)
        await session.flush()
        run_id = uuid.uuid7()
        one, two = b"<html>one</html>", b"<html>two</html>"
        first = await ingest.store(session, store, page.id, one, "text/html", run_id=run_id)
        again = await ingest.store(session, store, page.id, one, "text/html", run_id=run_id)
        changed = await ingest.store(session, store, page.id, two, "text/html", run_id=run_id)
        snapshots = list(await session.scalars(select(WebpageSnapshot)))
        return first, again, changed, snapshots


def test_the_same_bytes_are_kept_once_per_webpage(db: Database, object_store: MemoryObjectStore):
    first, again, changed, snapshots = db.run(_store_three_versions, db, object_store)

    assert first is not None
    assert again is None
    assert changed is not None
    assert {s.id for s in snapshots} == {first, changed}
    by_id = {s.id: s for s in snapshots}
    assert by_id[first].content_hash == hashlib.sha256(b"<html>one</html>").hexdigest()
    assert by_id[first].size_bytes == len(b"<html>one</html>")
    assert by_id[first].media_type == "text/html"
    assert sorted(k for k in object_store.objects if k.startswith("bytes/")) == sorted(
        [f"bytes/{first}", f"bytes/{changed}"]
    )
    assert object_store.objects[f"bytes/{first}"] == (b"<html>one</html>", "text/html")


def test_a_new_html_snapshot_is_parsed_to_markdown(db: Database, object_store: MemoryObjectStore):
    first, _, changed, snapshots = db.run(_store_three_versions, db, object_store)

    assert first is not None
    by_id = {s.id: s for s in snapshots}
    assert by_id[first].text_status is TextStatus.READY
    assert by_id[first].parser == "html:compact@1"
    assert object_store.objects[f"text/{first}/1"][0] == b"one\n"
    assert object_store.objects[f"text/{changed}/1"][0] == b"two\n"
