"""What every process works with: the settings, the database, the object store,
the job queue, and the crawler's HTTP client, opened once by `build_resources`
and passed on from there.

The API's lifespan, the worker, and the tests call `build_resources` with their own
settings. Nothing reads settings or opens a connection at import time.
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx
from procrastinate import App
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from gov_mine.config import Settings
from gov_mine.db.session import create_engine
from gov_mine.integrations.ai import jev
from gov_mine.integrations.http import create_http_client
from gov_mine.integrations.storage import ObjectStore, create_object_store
from gov_mine.jobs import create_app

if TYPE_CHECKING:
    from procrastinate import JobContext
    from procrastinate.connector import BaseConnector

# Where a worker's `additional_context` holds the resources.
KEY = "resources"


@dataclass(frozen=True, slots=True)
class Resources:
    settings: Settings
    engine: AsyncEngine
    # Tests swap in a factory whose sessions join one transaction.
    session_factory: Callable[[], AsyncSession]
    object_store: ObjectStore
    # The job queue: `defer` queues through it and the worker serves it.
    jobs: App
    # The crawler's client for the websites it fetches.
    http: httpx.AsyncClient
    # The client for model providers (OpenRouter's Decisions API).
    models_http: httpx.AsyncClient

    def session(self) -> AsyncSession:
        """A new session. One per request or job run; commit explicitly."""
        return self.session_factory()


@asynccontextmanager
async def build_resources(
    settings: Settings,
    *,
    object_store: ObjectStore | None = None,
    jobs_connector: BaseConnector | None = None,
    http: httpx.AsyncClient | None = None,
    models_http: httpx.AsyncClient | None = None,
) -> AsyncGenerator[Resources]:
    """Open every resource from `settings` and close them on exit. The engine
    connects lazily; the object store and the job queue open their pools here.
    Tests pass doubles: an in-memory store, an in-memory queue, and HTTP
    clients over mock transports."""
    engine = create_engine(settings)
    # Attributes stay readable after commit; async code cannot lazy-reload them.
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    jobs = create_app(settings, connector=jobs_connector)
    async with AsyncExitStack() as stack:
        stack.push_async_callback(engine.dispose)
        if object_store is None:
            object_store = await stack.enter_async_context(create_object_store(settings))
        await stack.enter_async_context(jobs.open_async())
        if http is None:
            http = await stack.enter_async_context(create_http_client())
        if models_http is None:
            models_http = await stack.enter_async_context(jev.create_client())
        yield Resources(
            settings=settings,
            engine=engine,
            session_factory=session_factory,
            object_store=object_store,
            jobs=jobs,
            http=http,
            models_http=models_http,
        )


def worker_context(resources: Resources) -> dict[str, Any]:
    """The `additional_context` to start a worker with."""
    return {KEY: resources}


def resources_of(context: JobContext) -> Resources:
    """The resources the worker running this job was started with."""
    found: Resources = context.additional_context[KEY]
    return found


__all__ = ["KEY", "Resources", "build_resources", "resources_of", "worker_context"]
