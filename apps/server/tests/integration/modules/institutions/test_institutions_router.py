from typing import TYPE_CHECKING

from sqlalchemy import select

from gov_mine.modules.crawl.models import CrawlPolicy, Domain

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from tests.integration.conftest import Database

CITY = {
    "name": "City of Example",
    "institution_type": "city",
    "website_url": "https://www.example.gov/",
    "country_code": "US",
    "state": "Ohio",
    "city": "Example",
}


async def _policy(db: Database, name: str) -> CrawlPolicy | None:
    async with db.session() as session:
        return await session.scalar(select(Domain.crawl_policy).where(Domain.name == name))


async def _block(db: Database, name: str) -> None:
    async with db.session() as session:
        session.add(Domain(name=name, crawl_policy=CrawlPolicy.BLOCKED))
        await session.commit()


def test_an_added_institution_is_listed_and_its_host_is_crawled(client: TestClient, db: Database):
    db.run(_block, db, "www.example.gov")

    created = client.post("/institutions", json=CITY)
    listed = client.get("/institutions").json()

    assert created.status_code == 201
    assert listed["total"] == 1
    [row] = listed["items"]
    assert row["name"] == "City of Example"
    assert row["website_url"] == "https://www.example.gov/"
    assert row["last_run"] is None
    assert row["next_run_at"] is None
    assert db.run(_policy, db, "www.example.gov") == CrawlPolicy.CRAWL


def test_editing_changes_the_name_type_and_location(client: TestClient, db: Database):
    institution_id = client.post("/institutions", json=CITY).json()["id"]

    edited = client.put(
        f"/institutions/{institution_id}",
        json={**CITY, "name": "Example County", "institution_type": "county", "city": None},
    ).json()

    assert edited["name"] == "Example County"
    assert edited["institution_type"] == "county"
    assert edited["city"] is None
    assert db.run(_policy, db, "www.example.gov") == CrawlPolicy.CRAWL


def test_a_website_that_is_not_http_or_a_missing_name_is_refused(client: TestClient):
    ftp = client.post("/institutions", json={**CITY, "website_url": "ftp://example.gov/"})
    nameless = client.post("/institutions", json={**CITY, "name": "  "})

    assert ftp.status_code == 422
    assert ftp.json()["detail"][0]["loc"] == ["body", "website_url"]
    assert nameless.status_code == 422
    assert client.get("/institutions").json()["total"] == 0
