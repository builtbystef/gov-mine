"""The crawl's jobs. Each carries its run's `run_id`, which is how `crawl.finish` knows the run
has work left."""

import uuid

from gov_mine.jobs.tasks import task
from gov_mine.modules.crawl import service
from gov_mine.resources import Resources


@task(service.START_TASK)
async def start(res: Resources, *, run_id: str) -> None:
    async with res.session() as session:
        await service.start_run(session, res.http, uuid.UUID(run_id))
        await session.commit()


@task(service.FETCH_TASK)
async def fetch(res: Resources, *, run_id: str, webpage_id: str, depth: int) -> None:
    async with res.session() as session:
        await service.fetch_page(
            session,
            res.http,
            res.object_store,
            run_id=uuid.UUID(run_id),
            webpage_id=uuid.UUID(webpage_id),
            depth=depth,
        )
        await session.commit()


@task(service.FINISH_TASK)
async def finish(res: Resources, *, run_id: str) -> None:
    async with res.session() as session:
        await service.finish_run(session, uuid.UUID(run_id))
        await session.commit()
