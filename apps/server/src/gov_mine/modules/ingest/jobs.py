"""The ingest jobs. `ingest.parse` carries its run's `run_id`, so the run finishes after it."""

import uuid

from gov_mine.jobs.tasks import task
from gov_mine.modules.ingest import service
from gov_mine.resources import Resources


@task(service.PARSE_TASK)
async def parse(res: Resources, *, run_id: str, snapshot_id: str) -> None:  # noqa: ARG001
    async with res.session() as session:
        await service.parse(session, res.object_store, uuid.UUID(snapshot_id))
        await session.commit()
