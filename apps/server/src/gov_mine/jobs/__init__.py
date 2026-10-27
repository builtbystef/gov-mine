"""The job queue: Procrastinate on the app's PostgreSQL, no broker.

Tasks are registered at import time on `registry`, a Blueprint that needs no
settings. A process gets an `App` from `create_app(settings)` (through
`build_resources`), which imports every task module and binds the registry to it.
"""

from typing import TYPE_CHECKING

from procrastinate import App, Blueprint, PsycopgConnector
from sqlalchemy.engine import make_url

if TYPE_CHECKING:
    from procrastinate.connector import BaseConnector

    from gov_mine.config import Settings

# Imported by `create_app` before the registry is bound, so every task is
# registered. A domain task lives in a `jobs.py` next to what it works on and is
# listed here; the tasks in this package are about the platform.
TASK_MODULES = [
    "gov_mine.jobs.stalled",
]

# What every `@task` registers on. Import-time, settings-free.
registry = Blueprint()


def conninfo(settings: Settings) -> str:
    """The database URL for psycopg itself: no SQLAlchemy driver in the scheme."""
    url = make_url(str(settings.database_url)).set(drivername="postgresql")
    return url.render_as_string(hide_password=False)


def create_app(settings: Settings, *, connector: BaseConnector | None = None) -> App:
    """An `App` over `settings`' database (or `connector`, which tests pass
    in-memory), with every task in `TASK_MODULES` registered."""
    app = App(
        connector=connector
        or PsycopgConnector(
            conninfo=conninfo(settings), min_size=1, max_size=settings.database_pool_size
        ),
        import_paths=TASK_MODULES,
        # A job that succeeded is dropped from the table; one that failed stays
        # to be looked at (`procrastinate shell`).
        worker_defaults={"delete_jobs": "successful"},
    )
    app.perform_import_paths()
    bind(app, registry)
    return app


def bind(app: App, registry: Blueprint) -> None:
    """Register `registry`'s tasks on `app` under their own names.

    Procrastinate's `add_tasks_from` prefixes a namespace and renames the
    registry's tasks in place, so it can run once per registry. This runs once
    per app, so each process, and each test, builds its own app over the one
    registry. A task's back-link (what `defer` queues through) points at the app
    built last: the one app of a worker, or the current test's.
    """
    for task in set(registry.tasks.values()):
        task.blueprint = app
    app.tasks.update(registry.tasks)
    for periodic in registry.periodic_registry.periodic_tasks.values():
        app.periodic_registry.register_task(
            task=periodic.task,
            cron=periodic.cron,
            periodic_id=periodic.periodic_id,
            configure_kwargs=periodic.configure_kwargs,
        )


__all__ = ["TASK_MODULES", "bind", "conninfo", "create_app", "registry"]
