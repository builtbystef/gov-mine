import json
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from gov_mine.modules.classify.models import Document
from gov_mine.modules.crawl.models import CrawlPolicy, CrawlRun, Domain, RunStatus, Webpage
from gov_mine.modules.export import service as exports
from gov_mine.modules.extract.models import (
    Citation,
    Extraction,
    Record,
    RecordSnapshot,
    RecordType,
)
from gov_mine.modules.ingest.models import TextStatus, WebpageSnapshot
from gov_mine.modules.institutions.models import DocumentType, Institution, InstitutionType

if TYPE_CHECKING:
    from pathlib import Path

    from tests.integration.conftest import Database

NOW = datetime(2026, 10, 27, 12, tzinfo=UTC)
FILES = [
    "citations.jsonl",
    "contacts.jsonl",
    "contracts.jsonl",
    "documents.jsonl",
    "grants.jsonl",
    "manifest.json",
    "meetings.jsonl",
    "news_items.jsonl",
    "projects.jsonl",
    "rfps.jsonl",
]
HUB = {"name": "Parkdale Hub", "phase": "Delivery and Construction", "start_date": "2024-03-01"}


async def _seed(db: Database) -> str:
    """CreateTO with a finished run and three documents: a project page dated 2024 with a cited
    record (under an undated listing document), and a 2019 news release with a record."""
    async with db.session() as session:
        institution = Institution(
            name="CreateTO",
            institution_type=InstitutionType.MUNICIPAL_AGENCY,
            website_url="https://createto.ca/",
        )
        domain = Domain(name="createto.ca", crawl_policy=CrawlPolicy.CRAWL)
        session.add_all([institution, domain])
        await session.flush()
        run = CrawlRun(
            institution_id=institution.id,
            status=RunStatus.FINISHED,
            settings={"trigger": "cli", "mode": "full"},
            started_at=NOW,
            finished_at=NOW,
        )
        pages = {
            name: Webpage(url=f"https://createto.ca/{name}", domain_id=domain.id)
            for name in ("projects", "projects/hub", "news/old")
        }
        session.add_all([run, *pages.values()])
        await session.flush()
        listing = Document(
            institution_id=institution.id,
            webpage_id=pages["projects"].id,
            document_type=DocumentType.PROJECTS,
            title="Projects",
        )
        session.add(listing)
        await session.flush()
        hub = Document(
            institution_id=institution.id,
            webpage_id=pages["projects/hub"].id,
            parent_document_id=listing.id,
            document_type=DocumentType.PROJECTS,
            title="Parkdale Hub",
            document_date=datetime(2023, 2, 2, tzinfo=UTC),
        )
        old = Document(
            institution_id=institution.id,
            webpage_id=pages["news/old"].id,
            document_type=DocumentType.PRESS_RELEASES,
            title="Old news",
            document_date=datetime(2019, 6, 1, tzinfo=UTC),
        )
        session.add_all([hub, old])
        await session.flush()

        async def record(document: Document, record_type: RecordType, data: dict[str, Any]) -> str:
            snapshot = WebpageSnapshot(
                webpage_id=document.webpage_id,
                content_hash=str(document.id).replace("-", "") * 2,
                media_type="text/html",
                size_bytes=1,
                text_status=TextStatus.READY,
            )
            session.add(snapshot)
            await session.flush()
            extraction = Extraction(
                crawl_run_id=run.id,
                snapshot_id=snapshot.id,
                record_type=record_type,
                extractor=f"model:{record_type}@1",
            )
            row = Record(
                record_type=record_type,
                institution_id=institution.id,
                document_id=document.id,
                key="",
            )
            session.add_all([extraction, row])
            await session.flush()
            state = RecordSnapshot(record_id=row.id, extraction_id=extraction.id, data=data)
            session.add(state)
            await session.flush()
            session.add_all(
                Citation(
                    record_snapshot_id=state.id,
                    field=field,
                    page=1,
                    excerpt=f"{value} excerpt",
                    verified=field == "name",
                )
                for field, value in data.items()
            )
            return str(row.id)

        hub_record = await record(hub, RecordType.PROJECT, HUB)
        await record(old, RecordType.NEWS_ITEM, {"headline": "Old", "published_at": "2019-06-01"})
        await session.commit()
        return hub_record


async def _export(db: Database, out: Path, since: date | None = None) -> dict[str, Any]:
    async with db.session() as session:
        return await exports.export(session, out, since=since, now=NOW)


def _lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_export_writes_records_documents_citations_and_a_manifest_within_the_window(
    db: Database, tmp_path: Path
):
    hub_record = db.run(_seed, db)

    manifest = db.run(_export, db, tmp_path / "a")

    assert sorted(path.name for path in (tmp_path / "a").iterdir()) == FILES
    # The 2019 release and its record are left out; the undated listing is kept. The project
    # page's date is its record's start date, later than its own.
    documents = _lines(tmp_path / "a" / "documents.jsonl")
    assert [(d["url"], d["document_date"], d["parent"]) for d in documents] == [
        ("https://createto.ca/projects", None, None),
        ("https://createto.ca/projects/hub", "2024-03-01", "https://createto.ca/projects"),
    ]
    assert set(documents[1]) == {
        "id",
        "institution",
        "url",
        "document_type",
        "title",
        "document_date",
        "parent",
        "first_seen_at",
    }
    assert documents[1]["institution"] == "CreateTO"
    [project] = _lines(tmp_path / "a" / "projects.jsonl")
    assert project["id"] == hub_record
    assert (project["institution"], project["document"], project["key"]) == (
        "CreateTO",
        "https://createto.ca/projects/hub",
        "",
    )
    assert {field: project[field] for field in HUB} == HUB
    assert project["citations"][0] == {
        "field": "name",
        "url": "https://createto.ca/projects/hub",
        "page": 1,
        "excerpt": "Parkdale Hub excerpt",
        "verified": True,
    }
    assert project["first_seen_at"] is not None
    assert project["last_changed_at"] is not None
    assert _lines(tmp_path / "a" / "news_items.jsonl") == []
    citations = _lines(tmp_path / "a" / "citations.jsonl")
    assert [(c["record"], c["field"]) for c in citations] == [
        (hub_record, "name"),
        (hub_record, "phase"),
        (hub_record, "start_date"),
    ]

    assert manifest == json.loads((tmp_path / "a" / "manifest.json").read_text())
    assert manifest["cutoff"] == "2021-10-27"
    assert manifest["exported_at"] == NOW.isoformat()
    assert [run["institution"] for run in manifest["runs"]] == ["CreateTO"]
    assert manifest["extractors"] == ["model:project@1"]
    assert manifest["files"]["projects.jsonl"] == 1
    assert manifest["files"]["documents.jsonl"] == 2
    assert manifest["files"]["citations.jsonl"] == 3

    # Exporting again gives the same lines.
    db.run(_export, db, tmp_path / "b")
    for name in FILES:
        if name.endswith(".jsonl"):
            assert (tmp_path / "a" / name).read_text() == (tmp_path / "b" / name).read_text()


def test_since_moves_the_cutoff(db: Database, tmp_path: Path):
    db.run(_seed, db)

    manifest = db.run(_export, db, tmp_path, date(2025, 1, 1))

    assert manifest["cutoff"] == "2025-01-01"
    assert [d["url"] for d in _lines(tmp_path / "documents.jsonl")] == [
        "https://createto.ca/projects"
    ]
    assert _lines(tmp_path / "projects.jsonl") == []
