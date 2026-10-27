import json
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select

from gov_mine.main import create_app
from gov_mine.modules.classify.models import Classification, Document, Source
from gov_mine.modules.crawl.models import CrawlPolicy, CrawlRun, Domain, Webpage
from gov_mine.modules.ingest import service as ingest
from gov_mine.modules.ingest.models import WebpageSnapshot
from gov_mine.modules.institutions.models import DocumentType, Institution, InstitutionType
from gov_mine.modules.ledger.models import AICall, AIPurpose

if TYPE_CHECKING:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from tests.integration.conftest import Database, InlineConnector, OpenRouter

    from gov_mine.config import Settings
    from gov_mine.integrations.storage.memory import MemoryObjectStore

KEY = "sk-or-test-not-a-real-key"
NEWS = "https://createto.ca/news"
RELEASE = "https://createto.ca/news/budget-approved"
ABOUT = "https://createto.ca/about"
ANSWERS = {NEWS: "listing:press_releases", RELEASE: "document:press_releases", ABOUT: "none"}


class Jev:
    """OpenRouter's Decisions API: answers by the page's URL, or fails `failures` times."""

    def __init__(self, failures: int = 0) -> None:
        self.requests: list[dict] = []
        self.failures = failures

    def __call__(self, request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://openrouter.ai/api/alpha/decisions"
        assert request.headers["Authorization"] == f"Bearer {KEY}"
        body = json.loads(request.content)
        self.requests.append(body)
        if len(self.requests) <= self.failures:
            return httpx.Response(502, json={"error": {"message": "Provider returned error"}})
        choice = ANSWERS[body["state"]["url"]]
        probabilities = dict.fromkeys(body["questions"]["page_type"]["criteria"], 0.0)
        probabilities["listing:projects"] = 0.1
        probabilities[choice] = 0.9
        return httpx.Response(
            200,
            json={
                "id": "gen-dec-1",
                "model": "typesafe/jev-1.14-20261014",
                "provider": "TypeSafe",
                "answers": {
                    "page_type": {
                        "type": "choice",
                        "choice": choice,
                        "probabilities": probabilities,
                        "confidence": 0.8,
                    }
                },
                "usage": {"input_tokens": 1000, "output_tokens": 50, "cost": 0.000042},
            },
        )


@pytest.fixture
def jev() -> Jev:
    return Jev()


@pytest.fixture
def settings(settings: Settings) -> Settings:
    return settings.model_copy(update={"openrouter_api_key": SecretStr(KEY)})


@pytest.fixture
def app(
    settings: Settings,
    object_store: MemoryObjectStore,
    queue: InlineConnector,
    jev: Jev,
    openrouter: OpenRouter,
) -> FastAPI:
    # The release becomes a news document, which is extracted.
    openrouter.answers[RELEASE] = {"document_date": None, "records": []}
    return create_app(
        settings,
        object_store=object_store,
        jobs_connector=queue,
        models_http=httpx.AsyncClient(transport=httpx.MockTransport(jev)),
        extract_http=openrouter.client(),
    )


def _html(title: str, body: str) -> bytes:
    return f"<html><head><title>{title}</title></head><body>{body}</body></html>".encode()


PAGES = {
    NEWS: _html("News", f'<h1>News</h1><p>Latest releases.</p><a href="{RELEASE}">Budget</a>'),
    RELEASE: _html("Budget approved", "<h1>Budget approved</h1><p>The board approved it.</p>"),
    ABOUT: _html("About", "<h1>About CreateTO</h1><p>Who we are.</p>"),
}


async def _crawl(db: Database, store: MemoryObjectStore, urls: list[str]) -> uuid.UUID:
    """Store a snapshot of each page in one run, as its fetch would; parsing and classifying run
    inline."""
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
        session.add(run)
        await session.flush()
        pages: dict[str, Webpage] = {}
        for url in urls:
            found_on = pages[NEWS].id if url == RELEASE and NEWS in pages else None
            pages[url] = Webpage(url=url, domain_id=domain.id, discovered_from_webpage_id=found_on)
            session.add(pages[url])
            await session.flush()
            await ingest.store(
                session, store, pages[url].id, PAGES[url], "text/html", run_id=run.id
            )
        await session.commit()
        return run.id


async def _rows(db: Database, model: type) -> list:
    async with db.session() as session:
        return list(await session.scalars(select(model)))


async def _store_again(db: Database, store: MemoryObjectStore, run_id: uuid.UUID) -> None:
    async with db.session() as session:
        webpage = await session.scalar(select(Webpage).where(Webpage.url == NEWS))
        assert webpage is not None
        await ingest.store(
            session,
            store,
            webpage.id,
            PAGES[NEWS] + b"<!-- changed -->",
            "text/html",
            run_id=run_id,
        )
        await session.commit()


async def _snapshot(db: Database, url: str) -> WebpageSnapshot:
    async with db.session() as session:
        found = await session.scalar(
            select(WebpageSnapshot).join(Webpage).where(Webpage.url == url)
        )
        assert found is not None
        return found


def test_each_new_page_is_classified_once_into_a_source_or_document(
    db: Database, object_store: MemoryObjectStore, jev: Jev, client: TestClient
):
    run_id = db.run(_crawl, db, object_store, [NEWS, RELEASE, ABOUT])

    # 019: one classification and one classify call per page, the request as section 8 says.
    assert len(jev.requests) == 3
    request = jev.requests[0]
    assert request["model"] == "typesafe/jev-1.14"
    assert request["state"]["url"] == NEWS
    assert request["state"]["title"] == "News"
    assert request["state"]["links"] == [{"text": "Budget", "href": RELEASE}]
    assert "Latest releases." in request["state"]["text"]
    assert len(request["questions"]["page_type"]["criteria"]) == 25
    classifications = {c.choice: c for c in db.run(_rows, db, Classification)}
    assert set(classifications) == set(ANSWERS.values())
    listing = classifications["listing:press_releases"]
    assert listing.classifier == "jev:classify@1"
    assert listing.confidence == pytest.approx(0.9)
    assert listing.raw_output is not None
    assert listing.raw_output["confidence"] == 0.8
    assert len(listing.raw_output["probabilities"]) == 25
    # The release, a news document, is extracted too (023).
    calls = [c for c in db.run(_rows, db, AICall) if c.purpose is not AIPurpose.EXTRACT]
    assert {call.classification_id for call in calls} == {c.id for c in classifications.values()}
    assert all(call.purpose is AIPurpose.CLASSIFY for call in calls)
    # 1000 tokens at 0.042 per million, output free.
    assert {call.cost for call in calls} == {Decimal("0.000042")}

    # 020: the listing is a daily source, the release a document under it, `none` neither.
    [source] = db.run(_rows, db, Source)
    assert source.document_type is DocumentType.PRESS_RELEASES
    assert source.crawl_interval == timedelta(days=1)
    news = db.run(_snapshot, db, NEWS)
    assert source.next_crawl_at == news.created_at + timedelta(days=1)
    [document] = db.run(_rows, db, Document)
    assert document.document_type is DocumentType.PRESS_RELEASES
    assert document.title == "Budget approved"
    assert document.source_id == source.id
    assert document.institution_id == source.institution_id

    # A later snapshot of a classified page is not classified again.
    db.run(_store_again, db, object_store, run_id)
    assert len(jev.requests) == 3
    assert len(db.run(_rows, db, Classification)) == 3

    # The run's paid calls, sources and documents by type, over the API.
    ai_calls = client.get("/ai-calls", params={"run": str(run_id)}).json()
    assert ai_calls["total"] == 4
    assert [call["purpose"] for call in ai_calls["items"]].count("classify") == 3
    sources = client.get(f"/runs/{run_id}/sources").json()
    assert [(s["url"], s["document_type"]) for s in sources["items"]] == [(NEWS, "press_releases")]
    counts = client.get(f"/runs/{run_id}/document-counts").json()
    assert counts == [{"document_type": "press_releases", "count": 1}]


@pytest.mark.parametrize("jev", [Jev(failures=2)])
def test_a_provider_error_is_retried_once_then_recorded(
    db: Database, object_store: MemoryObjectStore, jev: Jev
):
    db.run(_crawl, db, object_store, [ABOUT])

    assert len(jev.requests) == 2
    [classification] = db.run(_rows, db, Classification)
    assert classification.choice is None
    assert classification.error is not None
    assert "502" in classification.error
    assert db.run(_rows, db, AICall) == []


async def _store_release(
    db: Database, store: MemoryObjectStore, run_id: uuid.UUID, data: bytes
) -> None:
    async with db.session() as session:
        webpage = await session.scalar(select(Webpage).where(Webpage.url == RELEASE))
        assert webpage is not None
        await ingest.store(session, store, webpage.id, data, "text/html", run_id=run_id)
        await session.commit()


def test_documents_are_listed_and_served_with_their_versions(
    db: Database, object_store: MemoryObjectStore, client: TestClient
):
    run_id = db.run(_crawl, db, object_store, [NEWS, RELEASE])
    # Same text, then new text: two versions from three snapshots.
    db.run(_store_release, db, object_store, run_id, PAGES[RELEASE] + b"<!-- same -->")
    changed = _html("Budget approved", "<h1>Budget approved</h1><p>The board amended it.</p>")
    db.run(_store_release, db, object_store, run_id, changed)

    page = client.get("/documents", params={"type": "press_releases"}).json()
    assert page["total"] == 1
    [summary] = page["items"]
    assert (summary["url"], summary["title"]) == (RELEASE, "Budget approved")
    assert client.get("/documents", params={"type": "projects"}).json()["total"] == 0
    assert client.get("/documents", params={"since": "2999-01-01"}).json()["total"] == 0

    document = client.get(f"/documents/{summary['id']}").json()
    assert (document["institution_name"], document["parent"]) == ("CreateTO", None)
    newest, oldest = document["versions"]
    assert newest["created_at"] > oldest["created_at"]
    assert newest["text_hash"] != oldest["text_hash"]
    assert client.get(f"/documents/{uuid.uuid4()}").status_code == 404
