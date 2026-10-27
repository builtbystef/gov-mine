"""`gov-mine`: the command line. Each command builds the resources as the API's
lifespan does and calls a service. With asgi.py, the one place that reads the
environment."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

import typer
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.config import Settings
from gov_mine.jobs import worker as jobs_worker
from gov_mine.modules.institutions import service as institutions
from gov_mine.modules.runs import service as runs
from gov_mine.resources import build_resources
from gov_mine.shared.exceptions import AppError

app = typer.Typer()
run_app = typer.Typer(help="Create crawl runs.")
app.add_typer(run_app, name="run")


@app.callback()
def main() -> None:
    """Crawl public institutions' websites and extract cited records."""


async def _in_transaction[T](settings: Settings, work: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Run `work` in one session over the configured resources and commit it."""
    async with build_resources(settings) as resources, resources.session() as session:
        result = await work(session)
        await session.commit()
        return result


def _run[T](work: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Run `work` in a transaction; an `AppError` is printed and exits 1 with nothing written."""
    try:
        return asyncio.run(_in_transaction(Settings(), work))
    except AppError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(1) from None


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


@app.command()
def seed() -> None:
    """Create the CreateTO institution and its domain, unless they exist. Prints its id."""
    result = _run(institutions.seed)
    institution = result.institution
    note = "created" if result.created else "already seeded"
    typer.echo(f"{institution.id}  {institution.name} ({note})")


@run_app.command("create")
def run_create(
    institution_id: Annotated[uuid.UUID, typer.Argument(help="The institution to crawl.")],
    full: Annotated[  # noqa: FBT002 - a Typer flag
        bool, typer.Option("--full", help="Crawl the whole site from the homepage.")
    ] = False,
) -> None:
    """Queue a run of the institution. Prints the run's id."""
    if not full:
        # Incremental runs come with sources; until then a run is always full.
        raise typer.BadParameter("only full runs exist yet: pass --full", param_hint="--full")
    run = _run(lambda session: runs.create_run(session, institution_id, trigger="cli", mode="full"))
    typer.echo(run.id)
