"""`gov-mine-worker`: the process that runs queued jobs. The one place, with asgi.py,
that reads the environment."""

import asyncio
import logging

from gov_mine.config import Settings
from gov_mine.resources import build_resources, worker_context
from gov_mine.shared import logs, telemetry

logger = logging.getLogger(__name__)


async def run(settings: Settings) -> None:
    logs.configure(settings.log_level, settings.log_format)
    if (log_handler := telemetry.configure(settings, service_name="gov-mine-worker")) is not None:
        logging.getLogger().addHandler(log_handler)
    async with build_resources(settings) as resources:
        jobs = resources.jobs
        logger.info("Worker ready: %d tasks registered", len(jobs.tasks))
        await jobs.run_worker_async(
            concurrency=settings.jobs_concurrency,
            additional_context=worker_context(resources),
        )


def main() -> None:
    asyncio.run(run(Settings()))


if __name__ == "__main__":
    main()
