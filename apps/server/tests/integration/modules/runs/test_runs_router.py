import uuid
from datetime import timedelta
from typing import TYPE_CHECKING

from gov_mine.db.base import utcnow
from gov_mine.modules.crawl.models import (
    CrawlPolicy,
    CrawlRun,
    Domain,
    Fetch,
    FetchOutcome,
    RunStatus,
    Webpage,
)
from gov_mine.modules.ingest.models import WebpageSnapshot
from gov_mine.modules.institutions.models import Institution, InstitutionType

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from tests.integration.conftest import Database

PAGE_KEYS = {"items", "total", "limit", "offset"}


async def _seed_runs(db: Database) -> dict[str, uuid.UUID]:
    """Two runs of one institution, the newer with a fetched homepage and a refused URL."""
    now = utcnow()
    async with db.session() as session:
        institution = Institution(
            name="CreateTO",
            institution_type=InstitutionType.MUNICIPAL_AGENCY,
            website_url="https://createto.ca/",
        )
        domain = Domain(name="createto.ca", crawl_policy=CrawlPolicy.CRAWL)
        session.add_all([institution, domain])
        await session.flush()
        older = CrawlRun(
            institution_id=institution.id,
            settings={"trigger": "cli", "mode": "full"},
            created_at=now - timedelta(hours=1),
        )
        newer = CrawlRun(
            institution_id=institution.id,
            status=RunStatus.FINISHED,
            settings={"trigger": "cli", "mode": "full", "limit": 25},
            created_at=now,
        )
        homepage = Webpage(url="https://createto.ca/", domain_id=domain.id)
        other = Webpage(url="https://createto.ca/elsewhere", domain_id=domain.id)
        session.add_all([older, newer, homepage, other])
        await session.flush()
        snapshot = WebpageSnapshot(
            webpage_id=homepage.id,
            content_hash="ab" * 32,
            media_type="text/html",
            size_bytes=1234,
        )
        session.add(snapshot)
        await session.flush()
        session.add_all(
            [
                Fetch(
                    crawl_run_id=newer.id,
                    webpage_id=homepage.id,
                    requested_at=now,
                    duration_ms=120,
                    outcome=FetchOutcome.FETCHED,
                    http_status=200,
                    snapshot_id=snapshot.id,
                ),
                Fetch(
                    crawl_run_id=newer.id,
                    webpage_id=other.id,
                    requested_at=now + timedelta(seconds=1),
                    outcome=FetchOutcome.SKIPPED_SCOPE,
                    reason="test",
                ),
            ]
        )
        await session.commit()
        return {"older": older.id, "newer": newer.id, "snapshot": snapshot.id}


def test_runs_are_listed_newest_first_a_page_at_a_time(client: TestClient, db: Database):
    ids = db.run(_seed_runs, db)

    first = client.get("/runs", params={"limit": 1}).json()
    second = client.get("/runs", params={"limit": 1, "offset": 1}).json()

    assert set(first) == PAGE_KEYS
    assert (first["total"], first["limit"], first["offset"]) == (2, 1, 0)
    assert (second["total"], second["limit"], second["offset"]) == (2, 1, 1)
    (newer,) = first["items"]
    (older,) = second["items"]
    assert newer["id"] == str(ids["newer"])
    assert newer["status"] == "finished"
    assert newer["institution_name"] == "CreateTO"
    assert newer["settings"] == {
        "trigger": "cli",
        "mode": "full",
        "limit": 25,
        "max_file_bytes": None,
        "extractors": None,
    }
    assert older["id"] == str(ids["older"])
    assert older["status"] == "queued"
    assert older["settings"] == {
        "trigger": "cli",
        "mode": "full",
        "limit": None,
        "max_file_bytes": None,
        "extractors": None,
    }


def test_a_runs_fetches_are_a_page_with_their_snapshots(client: TestClient, db: Database):
    ids = db.run(_seed_runs, db)

    page = client.get(f"/runs/{ids['newer']}/fetches").json()
    second = client.get(f"/runs/{ids['newer']}/fetches", params={"limit": 1, "offset": 1}).json()

    assert set(page) == PAGE_KEYS
    assert (page["total"], page["limit"], page["offset"]) == (2, 50, 0)
    fetched, skipped = page["items"]
    assert fetched["url"] == "https://createto.ca/"
    assert fetched["outcome"] == "fetched"
    assert fetched["http_status"] == 200
    assert fetched["duration_ms"] == 120
    assert fetched["snapshot"] == {
        "id": str(ids["snapshot"]),
        "content_hash": "ab" * 32,
        "media_type": "text/html",
        "size_bytes": 1234,
    }
    assert skipped["outcome"] == "skipped_scope"
    assert skipped["snapshot"] is None
    assert [item["id"] for item in second["items"]] == [skipped["id"]]
    assert client.get(f"/runs/{ids['older']}/fetches").json()["total"] == 0


def test_an_unknown_run_is_404(client: TestClient, db: Database):  # noqa: ARG001
    unknown = uuid.uuid4()
    assert client.get(f"/runs/{unknown}").status_code == 404
    assert client.get(f"/runs/{unknown}/fetches").status_code == 404


def test_a_page_larger_than_500_is_refused(client: TestClient):
    assert client.get("/runs", params={"limit": 501}).status_code == 422


def test_a_runs_counts_come_from_its_fetch_log(client: TestClient, db: Database):
    ids = db.run(_seed_runs, db)

    counts = client.get(f"/runs/{ids['newer']}").json()["counts"]

    assert counts == {
        "fetched": 1,
        "not_modified": 0,
        "skipped": 1,
        "blocked": 0,
        "failed": 0,
        "snapshots": 1,
        "cost": "0",
    }
