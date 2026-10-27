import asyncio
import json
import os
import re
import signal
import threading
from contextlib import suppress
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING

import click
import pytest
from procrastinate import App, PsycopgConnector
from procrastinate.schema import SchemaManager
from pydantic import PostgresDsn
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from typer.testing import CliRunner

from gov_mine.jobs import conninfo
from gov_mine.jobs.tasks import task
from gov_mine.resources import Resources

if TYPE_CHECKING:
    from collections.abc import Iterator

    import typer
    from sqlalchemy.engine import URL

    from gov_mine.config import Settings

REPO_ROOT = Path(__file__).parents[4]
# The worker runs on a database of its own: its queue is committed, not rolled back.
WORKER_DATABASE = "gov_mine_test_worker" + os.environ.get("TEST_DATABASE_SUFFIX", "")
# A worker the test expects to stop on its own is sent SIGTERM after this long.
WATCHDOG_SECONDS = 30
# Jobs at the cap wait this long for one more to start, which none should.
OVERFLOW_WINDOW = 0.5
# Jobs below the cap wait this long for the rest to start before giving up.
UNDERFLOW_TIMEOUT = 5


@dataclass
class Probe:
    """What the test jobs saw, run by the worker in this process."""

    cap: int = 0
    total: int = 0
    in_flight: int = 0
    peak: int = 0
    finished: int = 0
    released: asyncio.Event = field(default_factory=asyncio.Event)
    overflowed: asyncio.Event = field(default_factory=asyncio.Event)


probe = Probe()


def stop_worker() -> None:
    os.kill(os.getpid(), signal.SIGTERM)


@task("tests.cli.hold")
async def hold(_res: Resources) -> None:
    """Stays running until `probe.cap` jobs run at once (or it gives up), then a
    little longer, so a worker allowed more starts one more."""
    probe.in_flight += 1
    probe.peak = max(probe.peak, probe.in_flight)
    if probe.in_flight > probe.cap:
        probe.overflowed.set()
    try:
        if probe.in_flight == probe.cap and not probe.released.is_set():
            with suppress(TimeoutError):
                await asyncio.wait_for(probe.overflowed.wait(), OVERFLOW_WINDOW)
            probe.released.set()
        try:
            await asyncio.wait_for(probe.released.wait(), UNDERFLOW_TIMEOUT)
        except TimeoutError:
            probe.released.set()
    finally:
        probe.in_flight -= 1
        probe.finished += 1
        if probe.finished == probe.total:
            stop_worker()


@task("tests.cli.record")
async def record(_res: Resources) -> None:
    probe.finished += 1
    stop_worker()


def gov_mine() -> typer.Typer:
    """The `gov-mine` program, as installed."""
    (script,) = entry_points(group="console_scripts", name="gov-mine")
    cli: typer.Typer = script.load()
    return cli


def invoke(*args: str) -> tuple[int, str]:
    result = CliRunner().invoke(gov_mine(), list(args))
    # Rich styles the help when the environment forces color, as `vp run` does.
    return result.exit_code, click.unstyle(result.output)


@pytest.fixture(autouse=True)
def fresh_probe() -> None:
    global probe  # noqa: PLW0603
    probe = Probe()


@pytest.fixture
def worker_settings(
    settings: Settings, configured_url: URL, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Settings]:
    """An empty queue in a new database, which `gov-mine` reads from the environment."""
    worker_url = configured_url.set(database=WORKER_DATABASE).render_as_string(hide_password=False)
    admin = create_engine(configured_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{WORKER_DATABASE}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{WORKER_DATABASE}"'))
    worker_db = create_engine(worker_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    with worker_db.connect() as connection:
        connection.exec_driver_sql(SchemaManager.get_schema().replace("%", "%%"))
    worker_db.dispose()
    monkeypatch.setenv("GOV_MINE_DATABASE_URL", worker_url)
    try:
        yield settings.model_copy(update={"database_url": PostgresDsn(worker_url)})
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{WORKER_DATABASE}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def watchdog() -> Iterator[None]:
    """Stops a worker that would otherwise run for good, so the test fails instead of hanging."""
    timer = threading.Timer(WATCHDOG_SECONDS, stop_worker)
    timer.start()
    try:
        yield
    finally:
        timer.cancel()


def queue_jobs(settings: Settings, task_name: str, count: int) -> list[int]:
    async def defer_all() -> list[int]:
        app = App(connector=PsycopgConnector(conninfo=conninfo(settings)))
        async with app.open_async():
            deferrer = app.configure_task(task_name)
            return [await deferrer.defer_async() for _ in range(count)]

    return asyncio.run(defer_all())


def test_help_lists_the_worker_command():
    exit_code, output = invoke("--help")
    assert exit_code == 0
    # A row of the command list, not just the word: an app with only one command
    # would otherwise become that command, and still name it in its usage line.
    assert re.search(r"^\W*worker\s+\w", output, re.MULTILINE), output


def test_worker_help_documents_concurrency():
    exit_code, output = invoke("worker", "--help")
    assert exit_code == 0
    assert "--concurrency" in output


def test_gov_mine_is_installed_and_gov_mine_worker_is_not():
    installed = {
        script.name
        for script in entry_points(group="console_scripts")
        if script.dist is not None and script.dist.name == "gov-mine-server"
    }
    assert "gov-mine" in installed
    assert "gov-mine-worker" not in installed


def test_dev_starts_the_worker_through_gov_mine_worker():
    scripts: dict[str, str] = json.loads((REPO_ROOT / "package.json").read_text())["scripts"]
    assert "pnpm run dev:worker" in scripts["dev"]
    assert "gov-mine worker" in scripts["dev:worker"]
    assert not any("gov-mine-worker" in command for command in scripts.values())


@pytest.mark.usefixtures("worker_settings", "watchdog")
@pytest.mark.parametrize(
    "args",
    [
        pytest.param(["nope"], id="unknown command"),
        pytest.param(["worker", "--bogus"], id="unknown option"),
        pytest.param(["--bogus"], id="unknown top-level option"),
        pytest.param(["worker", "--concurrency", "three"], id="concurrency not a number"),
        pytest.param(["worker", "--concurrency", "0"], id="concurrency zero"),
        pytest.param(["worker", "--concurrency", "-1"], id="concurrency negative"),
        pytest.param(["worker", "extra"], id="unexpected argument"),
    ],
)
def test_bad_usage_exits_non_zero_without_starting_a_worker(args: list[str]):
    exit_code, output = invoke(*args)
    assert exit_code != 0, output
    assert probe.finished == 0


@pytest.mark.usefixtures("watchdog")
def test_worker_runs_queued_jobs_at_most_concurrency_at_once(
    worker_settings: Settings, monkeypatch: pytest.MonkeyPatch
):
    # A configured value other than the flag's, so the flag is seen to win.
    monkeypatch.setenv("GOV_MINE_JOBS_CONCURRENCY", "1")
    probe.cap, probe.total = 3, 4
    queue_jobs(worker_settings, "tests.cli.hold", probe.total)

    exit_code, output = invoke("worker", "--concurrency", "3")

    assert exit_code == 0, output
    assert probe.finished == 4
    assert probe.peak == 3


@pytest.mark.usefixtures("watchdog")
def test_worker_without_the_flag_runs_the_configured_concurrency(
    worker_settings: Settings, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("GOV_MINE_JOBS_CONCURRENCY", "4")
    probe.cap, probe.total = 4, 5
    queue_jobs(worker_settings, "tests.cli.hold", probe.total)

    exit_code, output = invoke("worker")

    assert exit_code == 0, output
    assert probe.finished == 5
    assert probe.peak == 4


@pytest.mark.usefixtures("watchdog")
def test_worker_runs_retry_stalled_which_requeues_a_dead_workers_job(worker_settings: Settings):
    (stalled,) = queue_jobs(worker_settings, "tests.cli.record", 1)
    # Left running by a worker since pruned: running, with no worker.
    engine = create_engine(
        str(worker_settings.database_url), isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    with engine.connect() as connection:
        connection.execute(
            text("UPDATE procrastinate_jobs SET status = 'doing' WHERE id = :id"), {"id": stalled}
        )
    engine.dispose()
    queue_jobs(worker_settings, "jobs.retry_stalled", 1)

    exit_code, output = invoke("worker")

    assert exit_code == 0, output
    assert probe.finished == 1
