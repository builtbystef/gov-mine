"""`classify.page`, queued by `ingest.parse` for a page's first snapshot with text; it queues
`extract.document` for a page that became a document."""

import uuid

from gov_mine.jobs.tasks import task
from gov_mine.modules.classify import service
from gov_mine.modules.extract import service as extract
from gov_mine.modules.ingest import service as ingest
from gov_mine.resources import Resources


@task(service.CLASSIFY_TASK)
async def page(res: Resources, *, run_id: str, snapshot_id: str) -> None:
    """Classify the page, then queue the extraction of the document it became, if any."""
    async with res.session() as session:
        classification = await service.classify_page(
            session,
            res.object_store,
            res.models_http,
            res.settings,
            run_id=uuid.UUID(run_id),
            snapshot_id=uuid.UUID(snapshot_id),
        )
        if classification is not None:
            snapshot = await ingest.get_snapshot(session, uuid.UUID(snapshot_id))
            await extract.queue_document(
                session, res.settings, uuid.UUID(run_id), snapshot.webpage_id
            )
        await session.commit()
