import pkgutil
from datetime import timedelta
from typing import TYPE_CHECKING

from procrastinate import PsycopgConnector, RetryStrategy
from procrastinate.schema import SchemaManager
from sqlalchemy import text

import gov_mine
from gov_mine.config import Settings
from gov_mine.db.base import utcnow
from gov_mine.jobs import TASK_MODULES, conninfo, create_app, registry
from gov_mine.jobs.stalled import retry_stalled
from gov_mine.jobs.tasks import RETRY_ON_ERROR, AnyTask, defer

if TYPE_CHECKING:
    from tests.integration.conftest import Database, InlineConnector


async def run_now(db: Database, task: AnyTask) -> int:
    """Defer `task` from a session on the test transaction; the inline worker runs it."""
    async with db.session() as session:
        return await defer(session, task)


def test_the_app_queues_through_the_database():
    settings = Settings(database_url="postgresql+psycopg://u:p@db:5432/gov_mine")
    assert conninfo(settings) == "postgresql://u:p@db:5432/gov_mine"
    created = create_app(settings)
    assert isinstance(created.connector, PsycopgConnector)
    assert created.import_paths == TASK_MODULES
    assert created.worker_defaults == {"delete_jobs": "successful"}
    # Every registered task is on it, and queues through it.
    assert set(registry.tasks) <= set(created.tasks)
    assert all(task.blueprint is created for task in registry.tasks.values())


def test_every_jobs_module_in_the_tree_is_registered():
    """A task in a `jobs.py` the worker does not import is never run."""
    found = {
        module.name
        for module in pkgutil.walk_packages(gov_mine.__path__, "gov_mine.")
        if module.name.endswith(".jobs") and not module.ispkg
    }
    listed = {module for module in TASK_MODULES if module.endswith(".jobs")}
    assert found == listed
    assert set(TASK_MODULES) - listed == {"gov_mine.jobs.stalled"}


def test_the_platform_tasks_are_registered_with_their_schedules():
    assert isinstance(RETRY_ON_ERROR, RetryStrategy)
    assert RETRY_ON_ERROR.max_attempts == 5
    periodic = {
        name: task.cron for (name, _), task in registry.periodic_registry.periodic_tasks.items()
    }
    assert periodic == {"jobs.retry_stalled": "*/10 * * * *"}
    assert registry.tasks["jobs.retry_stalled"] is retry_stalled


def test_a_job_is_queued_in_the_transaction_of_the_rows_it_is_about(
    db: Database, settings: Settings
):
    """Through the real connector (the in-memory one ignores the connection): the
    job row goes on the session's own connection, so it is rolled back, or
    committed, with the rest. The queue's tables are created in the test
    transaction and go with it."""
    real = create_app(settings)

    @real.task(name="tests.transactional")
    async def noop() -> None:
        pass

    async def scenario() -> tuple[int, int, list[int]]:
        if await db.connection.scalar(text("SELECT to_regclass('procrastinate_jobs')")) is None:
            await db.connection.exec_driver_sql(SchemaManager.get_schema().replace("%", "%%"))
        async with db.session() as session:
            rolled_back = await defer(session, noop)
            await session.rollback()
        async with db.session() as session:
            committed = await defer(session, noop)
            await session.commit()
        rows = await db.connection.scalars(
            text("SELECT id FROM procrastinate_jobs WHERE task_name = 'tests.transactional'")
        )
        return rolled_back, committed, list(rows)

    rolled_back, committed, rows = db.run(scenario)
    assert rolled_back != committed
    assert rows == [committed]


def test_retry_stalled_requeues_the_jobs_of_a_dead_worker(db: Database, queue: InlineConnector):
    """A job left running by a worker whose heartbeat stopped goes back to the
    queue (and, here, is run at once by the same worker); one held by a live
    worker is left alone."""
    dead, live = 1, 2
    long_ago = utcnow() - timedelta(minutes=5)
    queue.workers = {dead: long_ago, live: utcnow()}
    for job_id, worker_id in ((10, dead), (11, live)):
        queue.jobs[job_id] = {
            "id": job_id,
            "status": "doing",
            "task_name": "jobs.retry_stalled",
            "priority": 0,
            "lock": None,
            "queueing_lock": None,
            "args": {},
            "scheduled_at": None,
            "queue_name": "default",
            "attempts": 1,
            "worker_id": worker_id,
            "abort_requested": False,
        }
        queue.events[job_id] = [{"type": "started", "at": long_ago}]

    assert db.run(run_now, db, retry_stalled) > 0
    assert [e["type"] for e in queue.events[10]] == [
        "started",
        "scheduled",
        "deferred_for_retry",
        "started",
        "succeeded",
    ]
    assert queue.jobs[10]["status"] == "succeeded"
    assert queue.jobs[11]["status"] == "doing"
