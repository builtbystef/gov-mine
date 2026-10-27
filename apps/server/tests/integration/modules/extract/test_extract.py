import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import SecretStr
from sqlalchemy import select

from gov_mine.main import create_app
from gov_mine.modules.classify.models import Document
from gov_mine.modules.crawl.models import CrawlPolicy, CrawlRun, Domain, Webpage
from gov_mine.modules.extract import service as extract
from gov_mine.modules.extract.models import Citation, Extraction, Record, RecordSnapshot
from gov_mine.modules.ingest import service as ingest
from gov_mine.modules.institutions.models import DocumentType, Institution, InstitutionType
from gov_mine.modules.ledger.models import AICall, AIPurpose

if TYPE_CHECKING:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from tests.integration.conftest import Database, InlineConnector, OpenRouter

    from gov_mine.config import Settings
    from gov_mine.integrations.storage.memory import MemoryObjectStore

KEY = "sk-or-test-not-a-real-key"
RELEASE = "https://createto.ca/news/parkdale-hub-approved"
TEAM = "https://createto.ca/about/team"


def _html(body: str) -> bytes:
    return f"<html><head><title>T</title></head><body>{body}</body></html>".encode()


RELEASE_PAGE = _html(
    "<h1>Parkdale Hub approved</h1><p>Published October 1, 2026.</p>"
    "<p>The board approved the <strong>Parkdale Hub</strong> plan for 1,000 homes.</p>"
)
TEAM_PAGE = _html(
    "<h1>Our team</h1><ul><li>Ada Lovelace, Chief Executive Officer</li>"
    "<li>Grace Hopper, Director of Development</li><li>Alan Turing, Planner</li></ul>"
)


def _cited(value: Any, excerpt: str, page: int = 1) -> dict[str, Any]:
    return {"value": value, "page": page, "excerpt": excerpt}


NEWS_RECORD: dict[str, Any] = {
    "headline": _cited("Parkdale Hub approved", "Parkdale Hub approved"),
    "published_at": _cited("2026-10-01", "Published October 1, 2026."),
    # Not on the page: the quote check leaves it unverified.
    "summary": _cited("The board approved 2,000 homes.", "approved 2,000 homes at once"),
}
NEWS_ANSWER = {"document_date": "2026-10-01", "records": [NEWS_RECORD]}


def _person(name: str, title: str) -> dict[str, Any]:
    return {
        "name": _cited(name, f"{name}, {title}"),
        "title": _cited(title, f"{name}, {title}"),
        "email": None,
        "phone": None,
    }


ADA = _person("Ada Lovelace", "Chief Executive Officer")
TEAM_ANSWER = {
    "document_date": None,
    "records": [
        ADA,
        _person("Grace Hopper", "Director of Development"),
        _person("Alan Turing", "Planner"),
    ],
}


@pytest.fixture
def settings(settings: Settings) -> Settings:
    return settings.model_copy(update={"openrouter_api_key": SecretStr(KEY)})


@pytest.fixture
def app(
    settings: Settings,
    object_store: MemoryObjectStore,
    queue: InlineConnector,
    openrouter: OpenRouter,
) -> FastAPI:
    openrouter.answers |= {RELEASE: NEWS_ANSWER, TEAM: TEAM_ANSWER}
    return create_app(
        settings,
        object_store=object_store,
        jobs_connector=queue,
        extract_http=openrouter.client(),
    )


async def _document(db: Database, url: str, document_type: DocumentType) -> uuid.UUID:
    """A run, and a webpage that is a document already: storing a snapshot extracts it."""
    async with db.session() as session:
        institution = Institution(
            name="CreateTO",
            institution_type=InstitutionType.MUNICIPAL_AGENCY,
            website_url="https://createto.ca/",
        )
        domain = Domain(name="createto.ca", crawl_policy=CrawlPolicy.CRAWL)
        session.add_all([institution, domain])
        await session.flush()
        run = CrawlRun(institution_id=institution.id, settings={"trigger": "cli", "mode": "full"})
        webpage = Webpage(url=url, domain_id=domain.id)
        session.add_all([run, webpage])
        await session.flush()
        session.add(
            Document(
                institution_id=institution.id,
                webpage_id=webpage.id,
                document_type=document_type,
                title="T",
            )
        )
        await session.commit()
        return run.id


async def _store(
    db: Database, store: MemoryObjectStore, run_id: uuid.UUID, url: str, data: bytes
) -> None:
    async with db.session() as session:
        webpage = await session.scalar(select(Webpage).where(Webpage.url == url))
        assert webpage is not None
        await ingest.store(session, store, webpage.id, data, "text/html", run_id=run_id)
        await session.commit()


async def _rows(db: Database, model: type[Any]) -> list[Any]:
    async with db.session() as session:
        return list(await session.scalars(select(model).order_by(model.id)))


async def _current(db: Database) -> list:
    async with db.session() as session:
        return await extract.list_current_records(session)


async def _extract_again(
    db: Database, store: MemoryObjectStore, settings: Settings, run_id: uuid.UUID
) -> Extraction | None:
    async with db.session() as session:
        document = await session.scalar(select(Document))
        assert document is not None
        return await extract.extract_document(
            session, store, settings, run_id=run_id, document_id=document.id
        )


def test_a_news_document_is_extracted_with_a_cited_record(
    db: Database, object_store: MemoryObjectStore, openrouter: OpenRouter, settings: Settings
):
    run_id = db.run(_document, db, RELEASE, DocumentType.PRESS_RELEASES)
    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE)

    # Structured output with the record type's schema, and no tools.
    [request] = openrouter.requests
    assert request["model"] == "openai/gpt-6-luna"
    assert request["response_format"]["type"] == "json_schema"
    assert "tools" not in request
    [extraction] = db.run(_rows, db, Extraction)
    assert (extraction.extractor, extraction.fallback_reason) == ("model:news_item@1", "no_rule")
    assert extraction.crawl_run_id == run_id
    assert extraction.error is None
    [record] = db.run(_rows, db, Record)
    assert (record.record_type, record.key) == ("news_item", "")
    [snapshot] = db.run(_rows, db, RecordSnapshot)
    assert snapshot.data == {
        "headline": "Parkdale Hub approved",
        "published_at": "2026-10-01",
        "summary": "The board approved 2,000 homes.",
    }
    citations = {c.field: c for c in db.run(_rows, db, Citation)}
    assert {f: (c.page, c.verified) for f, c in citations.items()} == {
        "headline": (1, True),
        "published_at": (1, True),
        "summary": (1, False),
    }
    [call] = db.run(_rows, db, AICall)
    assert (call.purpose, call.extraction_id, call.cost) == (
        AIPurpose.EXTRACT,
        extraction.id,
        Decimal("0.0004"),
    )
    # The date the model read becomes the document's date, for the five-year window.
    [document] = db.run(_rows, db, Document)
    assert document.document_date == datetime(2026, 10, 1, tzinfo=UTC)
    [current] = db.run(_current, db)
    assert current.data == snapshot.data

    # 027: the same snapshot again makes no call and no extraction.
    assert db.run(_extract_again, db, object_store, settings, run_id) is None
    # Bytes changed, text did not: no call.
    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE + b"<!-- nonce 2 -->")
    assert len(openrouter.requests) == 1
    # Text changed, the model finds the same values: an extraction, no record snapshot.
    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE + b"<p>Updated.</p>")
    assert len(openrouter.requests) == 2
    assert len(db.run(_rows, db, Extraction)) == 2
    assert len(db.run(_rows, db, RecordSnapshot)) == 1
    # Text changed and one field with it: one new snapshot of the same record.
    openrouter.answers[RELEASE] = {
        **NEWS_ANSWER,
        "records": [
            {
                **NEWS_RECORD,
                "summary": _cited("The board approved 1,000 homes.", "plan for 1,000 homes"),
            }
        ],
    }
    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE + b"<p>Updated again.</p>")
    assert len(db.run(_rows, db, Record)) == 1
    first, second = db.run(_rows, db, RecordSnapshot)
    assert first.data["summary"] == "The board approved 2,000 homes."
    assert second.data["summary"] == "The board approved 1,000 homes."
    [current] = db.run(_current, db)
    assert (current.record_snapshot_id, current.data) == (second.id, second.data)


async def _date(db: Database, run_id: uuid.UUID, day: datetime) -> None:
    """The run's cutoff as a run created on 2026-10-27 records it, and the document's date."""
    async with db.session() as session:
        run = await session.get_one(CrawlRun, run_id)
        run.settings = {**run.settings, "cutoff": "2021-10-27"}
        document = await session.scalar(select(Document))
        assert document is not None
        document.document_date = day
        await session.commit()


def test_a_document_dated_before_the_runs_cutoff_is_not_extracted(
    db: Database, object_store: MemoryObjectStore, openrouter: OpenRouter
):
    run_id = db.run(_document, db, RELEASE, DocumentType.PRESS_RELEASES)
    db.run(_date, db, run_id, datetime(2019, 6, 1, tzinfo=UTC))

    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE)

    assert openrouter.requests == []
    assert db.run(_rows, db, Extraction) == []


def test_a_document_updated_within_the_window_is_extracted_and_takes_the_later_date(
    db: Database, object_store: MemoryObjectStore, openrouter: OpenRouter
):
    run_id = db.run(_document, db, RELEASE, DocumentType.PRESS_RELEASES)
    db.run(_date, db, run_id, datetime(2024, 1, 1, tzinfo=UTC))

    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE)

    assert len(openrouter.requests) == 1
    assert len(db.run(_rows, db, Record)) == 1
    # The model read 2026-10-01, later than the document's date.
    [document] = db.run(_rows, db, Document)
    assert document.document_date == datetime(2026, 10, 1, tzinfo=UTC)


def test_a_staff_directory_yields_a_contact_per_person(
    db: Database, object_store: MemoryObjectStore, openrouter: OpenRouter
):
    run_id = db.run(_document, db, TEAM, DocumentType.STAFF_DIRECTORY)
    db.run(_store, db, object_store, run_id, TEAM, TEAM_PAGE)

    records = db.run(_rows, db, Record)
    assert sorted((r.record_type, r.key) for r in records) == [
        ("contact", "Ada Lovelace"),
        ("contact", "Alan Turing"),
        ("contact", "Grace Hopper"),
    ]
    assert all(c.verified for c in db.run(_rows, db, Citation))

    # A later page without Alan Turing and with a new title for Grace Hopper.
    openrouter.answers[TEAM] = {
        "document_date": None,
        "records": [
            ADA,
            _person("Grace Hopper", "Vice President, Development"),
        ],
    }
    db.run(_store, db, object_store, run_id, TEAM, TEAM_PAGE.replace(b"Director of", b"VP,"))
    assert len(db.run(_rows, db, Record)) == 3
    assert len(db.run(_rows, db, RecordSnapshot)) == 4
    current = {row.key: row.data["title"] for row in db.run(_current, db)}
    assert current == {
        "Ada Lovelace": "Chief Executive Officer",
        "Grace Hopper": "Vice President, Development",
        "Alan Turing": "Planner",
    }


def test_a_failing_model_is_retried_once_then_recorded(
    db: Database, object_store: MemoryObjectStore, openrouter: OpenRouter
):
    openrouter.failures = 2
    run_id = db.run(_document, db, RELEASE, DocumentType.PRESS_RELEASES)
    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE)

    assert len(openrouter.requests) == 2
    [extraction] = db.run(_rows, db, Extraction)
    assert extraction.error is not None
    assert "502" in extraction.error
    assert db.run(_rows, db, Record) == []
    assert db.run(_rows, db, AICall) == []


def test_records_are_served_with_their_citations_and_history(
    client: TestClient, db: Database, object_store: MemoryObjectStore, openrouter: OpenRouter
):
    run_id = db.run(_document, db, RELEASE, DocumentType.PRESS_RELEASES)
    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE)
    changed = _cited("The board approved 1,000 homes.", "plan for 1,000 homes")
    openrouter.answers[RELEASE] = {**NEWS_ANSWER, "records": [{**NEWS_RECORD, "summary": changed}]}
    db.run(_store, db, object_store, run_id, RELEASE, RELEASE_PAGE + b"<p>Updated.</p>")

    page = client.get("/records", params={"type": "news_item"}).json()
    assert page["total"] == 1
    [summary] = page["items"]
    assert (summary["url"], summary["institution_name"]) == (RELEASE, "CreateTO")
    assert summary["data"]["summary"] == "The board approved 1,000 homes."
    assert client.get("/records", params={"type": "project"}).json()["total"] == 0

    record = client.get(f"/records/{summary['id']}").json()
    fields = {f["field"]: f for f in record["fields"]}
    assert list(fields) == ["headline", "published_at", "summary"]
    citation = fields["summary"]["citation"]
    assert (citation["url"], citation["page"]) == (RELEASE, 1)
    assert (citation["excerpt"], citation["verified"]) == ("plan for 1,000 homes", True)
    newest, oldest = record["history"]
    assert newest["changes"] == [
        {
            "field": "summary",
            "before": "The board approved 2,000 homes.",
            "after": "The board approved 1,000 homes.",
        }
    ]
    assert newest["snapshot_id"] == citation["snapshot_id"]
    assert [c["field"] for c in oldest["changes"]] == ["headline", "published_at", "summary"]
    assert client.get(f"/records/{uuid.uuid4()}").status_code == 404
