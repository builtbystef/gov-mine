"""The thin path end to end: `gov-mine seed`, `gov-mine run create --full`, a worker that
crawls the homepage, and the API that shows the run. On a database of its own, migrated to
head, because the worker's jobs commit. Only the website is faked: it serves the saved
CreateTO homepage."""

import asyncio
import hashlib
import time
import uuid
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click
import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from procrastinate.testing import InMemoryConnector
from pydantic import PostgresDsn
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from typer.testing import CliRunner

from gov_mine.cli import app as cli
from gov_mine.integrations.storage.memory import MemoryObjectStore
from gov_mine.main import create_app
from gov_mine.modules.crawl.models import CrawlRun, RunStatus
from gov_mine.resources import build_resources, worker_context

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import URL, Engine

    from gov_mine.config import Settings

SERVER_ROOT = Path(__file__).resolve().parents[4]
HOMEPAGE = (SERVER_ROOT / "fixtures" / "createto" / "homepage.html").read_bytes()
DATABASE = "gov_mine_test_crawl"
# The run must be finished well within this; it takes a few seconds.
DEADLINE_SECONDS = 30


def invoke(*args: str) -> tuple[int, str]:
    result = CliRunner().invoke(cli, list(args))
    return result.exit_code, click.unstyle(result.output)


@pytest.fixture
def crawl_settings(
    settings: Settings, configured_url: URL, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Settings]:
    """A new database at the latest migration, which `gov-mine` reads from the environment."""
    url = configured_url.set(database=DATABASE).render_as_string(hide_password=False)
    admin = create_engine(configured_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{DATABASE}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{DATABASE}"'))
    monkeypatch.setenv("GOV_MINE_DATABASE_URL", url)
    command.upgrade(
        Config(file_=SERVER_ROOT / "alembic.ini", toml_file=SERVER_ROOT / "pyproject.toml"), "head"
    )
    try:
        yield settings.model_copy(update={"database_url": PostgresDsn(url)})
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{DATABASE}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def database(crawl_settings: Settings) -> Iterator[Engine]:
    engine = create_engine(str(crawl_settings.database_url), poolclass=NullPool)
    try:
        yield engine
    finally:
        engine.dispose()


def rows(engine: Engine, sql: str, **params: Any) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        return [dict(row._mapping) for row in connection.execute(text(sql), params)]  # noqa: SLF001


class Website:
    """Serves the saved homepage, and notes the run's status as each request arrives."""

    def __init__(self) -> None:
        self.requests: list[str] = []
        self.status_during_fetch: list[str] = []
        self.session_factory: Any = None

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(str(request.url))
        async with self.session_factory() as session:
            statuses = await session.scalars(text("SELECT status FROM crawl_runs"))
            self.status_during_fetch.extend(statuses)
        return httpx.Response(
            200, content=HOMEPAGE, headers={"Content-Type": "text/html; charset=utf-8"}
        )


async def crawl(settings: Settings, run_id: str, website: Website) -> MemoryObjectStore:
    """Run a worker until the run is no longer queued or running, and return what it stored."""
    store = MemoryObjectStore()
    async with (
        httpx.AsyncClient(transport=httpx.MockTransport(website)) as http,
        build_resources(settings, object_store=store, http=http) as resources,
    ):
        website.session_factory = resources.session
        worker = asyncio.create_task(
            resources.jobs.run_worker_async(
                install_signal_handlers=False,
                additional_context=worker_context(resources),
                # `crawl.finish` can then run while the fetch does, and must wait for it.
                concurrency=2,
                fetch_job_polling_interval=0.1,
            )
        )
        try:
            deadline = time.monotonic() + DEADLINE_SECONDS
            while time.monotonic() < deadline:
                async with resources.session() as session:
                    run = await session.get_one(CrawlRun, uuid.UUID(run_id))
                    if run.status not in {RunStatus.QUEUED, RunStatus.RUNNING}:
                        break
                await asyncio.sleep(0.1)
        finally:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker
    return store


def test_seed_creates_createto_once(database: Engine):
    first_code, first = invoke("seed")
    second_code, second = invoke("seed")

    assert (first_code, second_code) == (0, 0), first + second
    (institution,) = rows(database, "SELECT * FROM institutions")
    assert institution["name"] == "CreateTO"
    assert institution["institution_type"] == "municipal_agency"
    assert institution["website_url"] == "https://createto.ca/"
    assert str(institution["id"]) in first
    assert str(institution["id"]) in second
    (domain,) = rows(database, "SELECT * FROM domains")
    assert (domain["name"], domain["crawl_policy"]) == ("createto.ca", "crawl")


def test_run_create_with_an_unknown_institution_fails_and_creates_no_run(database: Engine):
    invoke("seed")

    exit_code, output = invoke("run", "create", str(uuid.uuid4()), "--full")

    assert exit_code != 0
    assert "No institution" in output
    assert rows(database, "SELECT * FROM crawl_runs") == []
    assert rows(database, "SELECT * FROM procrastinate_jobs WHERE task_name = 'crawl.start'") == []


def test_a_full_run_crawls_the_homepage_into_a_snapshot(crawl_settings: Settings, database: Engine):
    invoke("seed")
    (institution,) = rows(database, "SELECT id FROM institutions")

    exit_code, output = invoke("run", "create", str(institution["id"]), "--full")

    assert exit_code == 0, output
    run_id = output.strip()
    (run,) = rows(database, "SELECT * FROM crawl_runs WHERE id = :id", id=run_id)
    assert run["status"] == "queued"
    assert run["settings"] == {"trigger": "cli", "mode": "full"}
    assert run["institution_id"] == institution["id"]
    queued = rows(database, "SELECT task_name, args FROM procrastinate_jobs")
    assert [(job["task_name"], job["args"]["run_id"]) for job in queued] == [
        ("crawl.start", run_id)
    ]

    website = Website()
    store = asyncio.run(crawl(crawl_settings, run_id, website))

    # The run went running, then finished.
    assert website.requests == ["https://createto.ca/"]
    assert website.status_during_fetch == ["running"]
    (run,) = rows(database, "SELECT * FROM crawl_runs WHERE id = :id", id=run_id)
    assert run["status"] == "finished"
    assert run["started_at"] is not None
    assert run["finished_at"] is not None
    assert run["started_at"] <= run["finished_at"]
    # No job of the run is left.
    assert (
        rows(database, "SELECT * FROM procrastinate_jobs WHERE args->>'run_id' = :id", id=run_id)
        == []
    )

    # One fetch of the homepage, which wrote a snapshot.
    (fetch,) = rows(
        database,
        "SELECT f.*, w.url FROM fetches f JOIN webpages w ON w.id = f.webpage_id"
        " WHERE f.crawl_run_id = :id",
        id=run_id,
    )
    assert fetch["url"] == "https://createto.ca/"
    assert fetch["outcome"] == "fetched"
    assert fetch["http_status"] == 200
    assert fetch["duration_ms"] is not None
    assert fetch["duration_ms"] >= 0
    assert fetch["snapshot_id"] is not None
    assert run["finished_at"] > fetch["created_at"]

    # The bytes are in object storage under the snapshot's id; the row describes them.
    (snapshot,) = rows(database, "SELECT * FROM webpage_snapshots")
    assert snapshot["id"] == fetch["snapshot_id"]
    stored = store.objects[f"bytes/{snapshot['id']}"][0]
    assert stored == HOMEPAGE
    assert snapshot["content_hash"] == hashlib.sha256(HOMEPAGE).hexdigest()
    assert snapshot["media_type"] == "text/html"
    assert snapshot["size_bytes"] == len(stored)

    # The API shows the run and its fetch.
    with TestClient(
        create_app(crawl_settings, object_store=store, jobs_connector=InMemoryConnector())
    ) as client:
        runs = client.get("/runs").json()
        fetches = client.get(f"/runs/{run_id}/fetches").json()
    assert (runs["total"], runs["limit"], runs["offset"]) == (1, 50, 0)
    assert runs["items"][0]["id"] == run_id
    assert runs["items"][0]["status"] == "finished"
    assert fetches["total"] == 1
    (item,) = fetches["items"]
    assert item["outcome"] == "fetched"
    assert item["snapshot"]["id"] == str(snapshot["id"])
