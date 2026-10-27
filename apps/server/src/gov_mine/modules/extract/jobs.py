"""`extract.document`, queued by `classify.page` for a new document and by `ingest.parse` for a
later snapshot of one."""

import uuid

from gov_mine.jobs.tasks import task
from gov_mine.modules.extract import service
from gov_mine.resources import Resources


@task(service.EXTRACT_TASK)
async def document(res: Resources, *, run_id: str | None, document_id: str) -> None:
    async with res.session() as session:
        await service.extract_document(
            session,
            res.object_store,
            res.settings,
            run_id=None if run_id is None else uuid.UUID(run_id),
            document_id=uuid.UUID(document_id),
            http_client=res.extract_http,
        )
        await session.commit()
