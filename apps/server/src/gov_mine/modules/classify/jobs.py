"""`classify.page`, queued by `ingest.parse` for a page's first snapshot with text."""

import uuid

from gov_mine.jobs.tasks import task
from gov_mine.modules.classify import service
from gov_mine.resources import Resources


@task(service.CLASSIFY_TASK)
async def page(res: Resources, *, run_id: str, snapshot_id: str) -> None:
    async with res.session() as session:
        await service.classify_page(
            session,
            res.object_store,
            res.models_http,
            res.settings,
            run_id=uuid.UUID(run_id),
            snapshot_id=uuid.UUID(snapshot_id),
        )
        await session.commit()
