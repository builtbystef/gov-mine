"""`gov-mine`: the command line. Each command builds the resources as the API's
lifespan does and calls a service. With asgi.py, the one place that reads the
environment."""

import asyncio
from typing import Annotated

import typer

from gov_mine.config import Settings
from gov_mine.jobs import worker as jobs_worker

app = typer.Typer()


@app.callback()
def main() -> None:
    """Crawl public institutions' websites and extract cited records."""


@app.command()
def worker(
    concurrency: Annotated[
        int | None,
        typer.Option(min=1, show_default="GOV_MINE_JOBS_CONCURRENCY", help="Jobs run at once."),
    ] = None,
) -> None:
    """Run queued jobs until stopped."""
    settings = Settings()
    if concurrency is None:
        concurrency = settings.jobs_concurrency
    asyncio.run(jobs_worker.run(settings, concurrency))
