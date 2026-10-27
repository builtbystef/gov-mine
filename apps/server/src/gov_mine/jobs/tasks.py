"""`task`, the decorator that makes a job, and `defer`, which queues one."""

import functools
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Concatenate

from procrastinate import JobContext, RetryStrategy
from procrastinate.tasks import Task
from procrastinate.types import JSONValue

from gov_mine.jobs import registry
from gov_mine.jobs.context import Trace, running, trace
from gov_mine.resources import Resources, resources_of

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# For a job that fails on a flaky peer (a website, a model provider): five tries, the waits
# growing from a quarter of a minute to about four.
RETRY_ON_ERROR = RetryStrategy(max_attempts=5, wait=10, exponential_wait=4)

# Arguments after `Resources` are the job's, and must be JSON.
type JobFunction[**P, R] = Callable[Concatenate[Resources, P], Awaitable[R]]
# Positional arguments are not stored, so a task is always deferred with keywords.
type AnyTask = Task[Any, Any, Any]


def task(
    name: str, *, retry: RetryStrategy | None = None, cron: str | None = None
) -> Callable[[JobFunction[..., Any]], AnyTask]:
    """Register a job. `cron` makes it periodic (every worker fires it, the database
    keeps each tick to one run). A run gets the worker's `Resources` first, then the
    arguments it was queued with, and runs under the request ID and trace that
    queued it (see context.py)."""

    def decorator(func: JobFunction[..., Any]) -> AnyTask:
        @functools.wraps(func)
        async def run(
            context: JobContext, *, trace: Trace | None = None, **kwargs: JSONValue
        ) -> object:
            if cron is not None:
                # The tick, as Procrastinate sends it. No job here needs it.
                kwargs.pop("timestamp", None)
            with running(name, context.job.id, trace):
                return await func(resources_of(context), **kwargs)

        registered: AnyTask = registry.task(name=name, pass_context=True, retry=retry or False)(run)
        if cron is not None:
            registered = registry.periodic(cron=cron)(registered)
        return registered

    return decorator


async def defer(session: AsyncSession, task: AnyTask, **kwargs: JSONValue) -> int:
    """Queue one run in `session`'s transaction and return its job ID. The job row
    is written on the session's own connection, so it is committed, or rolled
    back, with the rows it is about; a worker is notified at commit, never before.
    (Sessions run on psycopg, which is the connection Procrastinate accepts; this
    would not survive a change of driver.) Goes through the `App` the task was
    last bound to (jobs/__init__.py): the process's one queue."""
    await session.flush()
    connection = await (await session.connection()).get_raw_connection()
    deferrer = task.configure(connection=connection.driver_connection)
    # `Trace` is `dict[str, str]`, which is not a `JSONValue` (dicts are invariant).
    carrier: dict[str, JSONValue] = {**trace()}
    return await deferrer.defer_async(trace=carrier, **kwargs)


__all__ = ["RETRY_ON_ERROR", "AnyTask", "JobFunction", "defer", "task"]
