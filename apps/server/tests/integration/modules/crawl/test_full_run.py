"""Full runs end to end: `gov-mine seed`, `gov-mine run create --full`, a worker that crawls
the site from the homepage, and the API that shows the run. On a database of its own, migrated
to head, because the worker's jobs commit. Only the website is faked: it serves the saved
CreateTO homepage, or a small site of its own."""

import asyncio
import hashlib
import json
import logging
import re
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
from gov_mine.shared.logs import ContextFilter, JsonFormatter

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
    """Serves `pages` (URL to body; a `.pdf` as a PDF, the rest as HTML) and 404 for the rest,
    and notes the run's status as each request arrives."""

    def __init__(self, pages: dict[str, bytes] | None = None) -> None:
        self.pages = pages if pages is not None else {"https://createto.ca/": HOMEPAGE}
        self.requests: list[str] = []
        self.status_during_fetch: list[str] = []
        self.session_factory: Any = None

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.requests.append(url)
        async with self.session_factory() as session:
            statuses = await session.scalars(text("SELECT status FROM crawl_runs"))
            self.status_during_fetch.extend(statuses)
        if url not in self.pages:
            return httpx.Response(404)
        media_type = "application/pdf" if url.endswith(".pdf") else "text/html; charset=utf-8"
        return httpx.Response(200, content=self.pages[url], headers={"Content-Type": media_type})


def page(*hrefs: str, script: str = "") -> bytes:
    """An HTML page linking to `hrefs`, with `script` as its `__NEXT_DATA__`."""
    links = "".join(f'<a href="{href}">link</a>' for href in hrefs)
    return (
        f'<html><body>{links}<script id="__NEXT_DATA__" type="application/json">{script}</script>'
        "</body></html>"
    ).encode()


def create_run(*options: str) -> str:
    """Seed CreateTO and create a full run of it with `options`; its id."""
    _, seeded = invoke("seed")
    exit_code, output = invoke("run", "create", seeded.split()[0], "--full", *options)
    assert exit_code == 0, output
    return output.strip()


def fetches_by_url(engine: Engine, run_id: str) -> dict[str, dict[str, Any]]:
    """The run's fetch rows by URL; a URL attempted twice fails the test."""
    fetches = rows(
        engine,
        "SELECT f.*, w.url FROM fetches f JOIN webpages w ON w.id = f.webpage_id"
        " WHERE f.crawl_run_id = :id",
        id=run_id,
    )
    by_url = {fetch["url"]: fetch for fetch in fetches}
    assert len(by_url) == len(fetches), "a URL was attempted twice"
    return by_url


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

    # The saved homepage links to the whole site: one request is enough here.
    exit_code, output = invoke("run", "create", str(institution["id"]), "--full", "--limit", "1")

    assert exit_code == 0, output
    run_id = output.strip()
    (run,) = rows(database, "SELECT * FROM crawl_runs WHERE id = :id", id=run_id)
    assert run["status"] == "queued"
    assert run["settings"] == {"trigger": "cli", "mode": "full", "limit": 1}
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


def test_a_runs_log_lines_carry_its_run_job_and_webpage_ids(
    crawl_settings: Settings, database: Engine, caplog: pytest.LogCaptureFixture
):
    invoke("seed")
    (institution,) = rows(database, "SELECT id FROM institutions")
    _, output = invoke("run", "create", str(institution["id"]), "--full", "--limit", "1")
    run_id = output.strip()

    caplog.handler.addFilter(ContextFilter())
    caplog.handler.setFormatter(JsonFormatter())
    with caplog.at_level(logging.INFO):
        asyncio.run(crawl(crawl_settings, run_id, Website()))

    lines = [json.loads(line) for line in caplog.text.splitlines()]
    job_done = re.compile(r"(crawl\.start|crawl\.fetch)\[(\d+)\] done in .*")
    done = [
        (match[1], int(match[2]), line)
        for line in lines
        if (match := job_done.fullmatch(line["message"]))
    ]
    (fetch,) = rows(database, "SELECT webpage_id FROM fetches")

    ((fetch_job_id, fetch_line),) = [
        (job_id, line)
        for task, job_id, line in done
        if task == "crawl.fetch" and line.get("webpage_id") == str(fetch["webpage_id"])
    ]
    assert fetch_line["run_id"] == run_id
    assert fetch_line["job_id"] == fetch_job_id
    assert fetch_line["webpage_id"] == str(fetch["webpage_id"])
    # The HTTP client's own line, written inside the fetch, carries the same.
    (request,) = [line for line in lines if line["logger"] == "httpx"]
    assert (request["run_id"], request["job_id"], request["webpage_id"]) == (
        run_id,
        fetch_job_id,
        str(fetch["webpage_id"]),
    )

    ((start_job_id, start_line),) = [
        (job_id, line) for task, job_id, line in done if task == "crawl.start"
    ]
    assert start_line["run_id"] == run_id
    assert start_line["job_id"] == start_job_id
    assert "webpage_id" not in start_line


SITE = "https://createto.ca"


def test_a_full_run_follows_links_within_the_site_once_each(
    crawl_settings: Settings, database: Engine
):
    run_id = create_run()
    website = Website(
        {
            f"{SITE}/": page(
                "/projects/",
                "/about#team",
                "https://elsewhere.example/page",
                "mailto:info@createto.ca",
                # Only in the embedded JSON, as createto.ca does with some files.
                script='{"filename":"https:\\/\\/createto.ca\\/files\\/report.pdf"}',
            ),
            f"{SITE}/projects": page("/", "/about", "/projects/a?utm_source=nav"),
            f"{SITE}/about": page("/projects", "https://createto.ca:443/projects/a"),
            f"{SITE}/projects/a": page(),
            f"{SITE}/files/report.pdf": b"%PDF-1.4",
        }
    )

    asyncio.run(crawl(crawl_settings, run_id, website))

    (run,) = rows(database, "SELECT status FROM crawl_runs")
    assert run["status"] == "finished"
    # Every page and file of the site requested once, under its normalised URL.
    assert sorted(website.requests) == [
        f"{SITE}/",
        f"{SITE}/about",
        f"{SITE}/files/report.pdf",
        f"{SITE}/projects",
        f"{SITE}/projects/a",
    ]
    # One row per URL, found on the page it was first seen on.
    webpages = rows(database, "SELECT id, url, discovered_from_webpage_id FROM webpages")
    ids = {webpage["url"]: webpage["id"] for webpage in webpages}
    found_on = {webpage["url"]: webpage["discovered_from_webpage_id"] for webpage in webpages}
    assert found_on == {
        f"{SITE}/": None,
        f"{SITE}/projects": ids[f"{SITE}/"],
        f"{SITE}/about": ids[f"{SITE}/"],
        f"{SITE}/files/report.pdf": ids[f"{SITE}/"],
        "https://elsewhere.example/page": ids[f"{SITE}/"],
        f"{SITE}/projects/a": ids[f"{SITE}/projects"],
    }
    # The other host's link is logged as refused, with no request.
    fetches = fetches_by_url(database, run_id)
    assert set(fetches) == set(ids)
    elsewhere = fetches.pop("https://elsewhere.example/page")
    assert (elsewhere["outcome"], elsewhere["reason"]) == ("skipped_scope", "other_host")
    assert (elsewhere["duration_ms"], elsewhere["http_status"]) == (None, None)
    assert {fetch["outcome"] for fetch in fetches.values()} == {"fetched"}
    (domain,) = rows(database, "SELECT crawl_policy FROM domains WHERE name = 'elsewhere.example'")
    assert domain["crawl_policy"] == "files_only"


def test_a_url_more_than_50_links_from_a_seed_is_not_requested(
    crawl_settings: Settings, database: Engine
):
    run_id = create_run()
    # A chain: the homepage links to /p/1, and /p/n to /p/n+1.
    pages = {f"{SITE}/": page("/p/1")}
    pages |= {f"{SITE}/p/{n}": page(f"/p/{n + 1}") for n in range(1, 60)}
    website = Website(pages)

    asyncio.run(crawl(crawl_settings, run_id, website))

    # /p/n is n links from the homepage: /p/50 is fetched, /p/51 is not.
    assert website.requests == [f"{SITE}/"] + [f"{SITE}/p/{n}" for n in range(1, 51)]
    fetches = fetches_by_url(database, run_id)
    deepest = fetches[f"{SITE}/p/51"]
    assert deepest["outcome"] == "skipped_depth"
    assert (deepest["duration_ms"], deepest["http_status"]) == (None, None)
    assert fetches[f"{SITE}/p/50"]["outcome"] == "fetched"
    assert len(fetches) == 52


def test_urls_outside_the_website_prefix_are_not_requested(
    crawl_settings: Settings, database: Engine
):
    run_id = create_run()
    with database.begin() as connection:
        connection.execute(
            text("UPDATE institutions SET website_url = 'https://createto.ca/projects/'")
        )
    website = Website(
        {
            f"{SITE}/projects": page(
                "/projects/a",
                "/projects-archive",
                "/about",
                "http://createto.ca/projects/b",
                "https://www.createto.ca/projects/c",
            ),
            f"{SITE}/projects/a": page(),
        }
    )

    asyncio.run(crawl(crawl_settings, run_id, website))

    assert sorted(website.requests) == [f"{SITE}/projects", f"{SITE}/projects/a"]
    refused = {
        url: (fetch["outcome"], fetch["reason"], fetch["duration_ms"])
        for url, fetch in fetches_by_url(database, run_id).items()
        if fetch["outcome"] != "fetched"
    }
    assert refused == {
        f"{SITE}/projects-archive": ("skipped_scope", "outside_prefix", None),
        f"{SITE}/about": ("skipped_scope", "outside_prefix", None),
        "http://createto.ca/projects/b": ("skipped_scope", "outside_prefix", None),
        "https://www.createto.ca/projects/c": ("skipped_scope", "other_host", None),
    }


def test_run_create_limit_caps_the_requests_the_run_sends(
    crawl_settings: Settings, database: Engine
):
    run_id = create_run("--limit", "3")
    (run,) = rows(database, "SELECT settings FROM crawl_runs")
    assert run["settings"] == {"trigger": "cli", "mode": "full", "limit": 3}
    pages = {f"{SITE}/": page("https://elsewhere.example/", *(f"/p/{n}" for n in range(10)))}
    pages |= {f"{SITE}/p/{n}": page(*(f"/p/{n}/{m}" for m in range(10))) for n in range(10)}
    website = Website(pages)

    asyncio.run(crawl(crawl_settings, run_id, website))

    (run,) = rows(database, "SELECT status FROM crawl_runs")
    assert run["status"] == "finished"
    assert len(website.requests) == 3
    fetches = fetches_by_url(database, run_id).values()
    assert len([fetch for fetch in fetches if fetch["duration_ms"] is not None]) == 3
    # The rest of the eleven links found wrote nothing, but a refusal, which costs no request.
    assert {fetch["outcome"] for fetch in fetches} <= {"fetched", "skipped_scope"}
    assert len(rows(database, "SELECT id FROM webpages")) > len(fetches)
