import uuid
from typing import TYPE_CHECKING

from gov_mine.modules.crawl.models import CrawlPolicy, Domain, Webpage
from gov_mine.modules.ingest import service as ingest
from gov_mine.modules.ingest.models import TextStatus, WebpageSnapshot

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.integration.conftest import Database

    from gov_mine.integrations.storage.memory import MemoryObjectStore

CORRUPT = b"%PDF-1.4\nnot a pdf"


async def _store_files(
    db: Database, store: MemoryObjectStore, files: dict[str, tuple[bytes, str]]
) -> dict[str, WebpageSnapshot]:
    async with db.session() as session:
        domain = Domain(name="a-us.storyblok.com", crawl_policy=CrawlPolicy.FILES_ONLY)
        session.add(domain)
        await session.flush()
        snapshots = {}
        for name, (data, media_type) in files.items():
            page = Webpage(url=f"https://a-us.storyblok.com/{name}", domain_id=domain.id)
            session.add(page)
            await session.flush()
            snapshot_id = await ingest.store(
                session, store, page.id, data, media_type, run_id=uuid.uuid7()
            )
            snapshots[name] = await session.get_one(WebpageSnapshot, snapshot_id)
            await session.refresh(snapshots[name])
        return snapshots


def test_files_get_a_text_object_per_page_none_or_a_failure(
    db: Database, object_store: MemoryObjectStore, make_pdf: Callable[..., bytes]
):
    files = {
        "pdf": (make_pdf("One", "Two", "Three"), "application/pdf"),
        "image": (b"\x89PNG\r\n\x1a\n", "image/png"),
        "corrupt": (CORRUPT, "application/pdf"),
    }

    snapshots = db.run(_store_files, db, object_store, files)

    pdf, image, corrupt = snapshots["pdf"], snapshots["image"], snapshots["corrupt"]
    assert (pdf.text_status, pdf.parser) == (TextStatus.READY, "pdf:markitdown@1")
    assert sorted(k for k in object_store.objects if k.startswith("text/")) == [
        f"text/{pdf.id}/{page}" for page in (1, 2, 3)
    ]
    assert object_store.objects[f"text/{pdf.id}/2"][0] == b"Two\n"
    assert image.text_status is TextStatus.NONE
    assert corrupt.text_status is TextStatus.FAILED
    assert corrupt.text_error
    assert "PdfiumError" in corrupt.text_error
    assert object_store.objects[f"bytes/{corrupt.id}"][0] == CORRUPT
