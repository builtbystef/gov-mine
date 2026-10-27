"""The ingest jobs. `ingest.parse` carries its run's `run_id`, so the run finishes after it, and
queues `classify.page` when the page has text and is not classified yet."""

import uuid

from gov_mine.jobs.tasks import task
from gov_mine.modules.classify import service as classify
from gov_mine.modules.ingest import service
from gov_mine.resources import Resources


@task(service.PARSE_TASK)
async def parse(res: Resources, *, run_id: str, snapshot_id: str) -> None:
    async with res.session() as session:
        await service.parse(session, res.object_store, uuid.UUID(snapshot_id))
        await classify.queue_page(session, res.settings, uuid.UUID(run_id), uuid.UUID(snapshot_id))
        await session.commit()
