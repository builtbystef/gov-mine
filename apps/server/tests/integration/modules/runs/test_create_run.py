import uuid
from typing import TYPE_CHECKING

import pytest
from procrastinate.testing import InMemoryConnector

from gov_mine.modules.crawl.models import CrawlRun, RunStatus
from gov_mine.modules.institutions.models import Institution, InstitutionType

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from tests.integration.conftest import Database

    from gov_mine.resources import Resources


class HeldConnector(InMemoryConnector):
    """The conftest's queue without running the jobs, so a created run stays `queued`."""

    def __init__(self) -> None:
        super().__init__()
        self.resources: Resources | None = None


@pytest.fixture
def queue() -> HeldConnector:
    return HeldConnector()


async def _institution_with_a_finished_run(db: Database) -> uuid.UUID:
    async with db.session() as session:
        institution = Institution(
            name="CreateTO",
            institution_type=InstitutionType.MUNICIPAL_AGENCY,
            website_url="https://createto.ca/",
        )
        session.add(institution)
        await session.flush()
        session.add(
            CrawlRun(
                institution_id=institution.id,
                status=RunStatus.FINISHED,
                settings={"trigger": "cli", "mode": "full"},
            )
        )
        await session.commit()
        return institution.id


def test_a_dashboard_run_is_queued_and_a_second_is_409(client: TestClient, db: Database):
    institution_id = db.run(_institution_with_a_finished_run, db)

    created = client.post("/runs", json={"institution_id": str(institution_id)})
    again = client.post("/runs", json={"institution_id": str(institution_id)})

    assert created.status_code == 201
    run = created.json()
    assert run["status"] == "queued"
    assert run["settings"]["trigger"] == "dashboard"
    assert run["elapsed_seconds"] is None
    assert again.status_code == 409
    assert client.get("/runs").json()["total"] == 2
