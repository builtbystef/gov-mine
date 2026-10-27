"""The process that runs queued jobs."""

import logging

from gov_mine.config import Settings
from gov_mine.resources import build_resources, worker_context
from gov_mine.shared import logs, telemetry

logger = logging.getLogger(__name__)

# How often an idle worker looks for a job it was not told about (Procrastinate's default is
# 5 s). A worker is told about new jobs, but not that a job's lock was released: a host's next
# fetch, locked behind the one that just ended, waits for this look.
FETCH_JOB_POLLING_SECONDS = 0.1


async def run(settings: Settings, concurrency: int) -> None:
    logs.configure(settings.log_level, settings.log_format)
    if (log_handler := telemetry.configure(settings, service_name="gov-mine-worker")) is not None:
        logging.getLogger().addHandler(log_handler)
    async with build_resources(settings) as resources:
        jobs = resources.jobs
        logger.info("Worker ready: %d tasks registered", len(jobs.tasks))
        await jobs.run_worker_async(
            concurrency=concurrency,
            fetch_job_polling_interval=FETCH_JOB_POLLING_SECONDS,
            additional_context=worker_context(resources),
        )
