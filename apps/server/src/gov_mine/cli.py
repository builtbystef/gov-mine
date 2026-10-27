"""`gov-mine`: the command line. Each command builds the resources as the API's
lifespan does and calls a service. With asgi.py, the one place that reads the
environment."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.config import Settings
from gov_mine.integrations.http.replay import replay_address, replay_app
from gov_mine.jobs import worker as jobs_worker
from gov_mine.modules.export import service as exports
from gov_mine.modules.institutions import service as institutions
from gov_mine.modules.runs import service as runs
from gov_mine.resources import build_resources
from gov_mine.shared.exceptions import AppError

app = typer.Typer()
run_app = typer.Typer(help="Create crawl runs and report on them.")
app.add_typer(run_app, name="run")
dev_app = typer.Typer(help="Development tools.")
app.add_typer(dev_app, name="dev")


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
    limit: Annotated[
        int | None, typer.Option(min=1, help="Send at most this many requests in the run.")
    ] = None,
    replay: Annotated[
        str | None,
        typer.Option(
            metavar="ADDRESS",
            help="Send every request to the replay server at this address (`gov-mine dev replay`).",
        ),
    ] = None,
) -> None:
    """Queue a run of the institution. Prints the run's id."""
    if not full:
        # Incremental runs come with sources; until then a run is always full.
        raise typer.BadParameter("only full runs exist yet: pass --full", param_hint="--full")
    if replay is not None:
        try:
            replay = replay_address(replay)
        except ValueError as exc:
            raise typer.BadParameter(str(exc), param_hint="--replay") from None
    run = _run(
        lambda session: runs.create_run(
            session, institution_id, trigger="cli", mode="full", limit=limit, replay=replay
        )
    )
    typer.echo(run.id)


@dev_app.command("replay")
def dev_replay(
    from_: Annotated[
        Path,
        typer.Option(
            "--from",
            exists=True,
            file_okay=False,
            help="The saved copies: a folder of bodies, each with its `<name>.meta.json`.",
        ),
    ],
    host: Annotated[str, typer.Option(help="The address to listen on.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="The port to listen on.")] = 8765,
    as_saved: Annotated[  # noqa: FBT002 - a Typer flag
        bool,
        typer.Option(
            "--as-saved", help="Serve the copies as saved, without the edited page and bad PDF."
        ),
    ] = False,
) -> None:
    """Serve the saved copies of every website for `run create --replay`, with one project
    page's phase changed and one PDF replaced by a corrupt file."""
    server = replay_app(from_, variants=not as_saved)
    typer.echo(f"Replaying {from_} at http://{host}:{port}")
    uvicorn.run(server, host=host, port=port, log_level="warning")


@run_app.command("report")
def run_report(
    run_id: Annotated[uuid.UUID, typer.Argument(help="The run to report on.")],
    as_json: Annotated[  # noqa: FBT002 - a Typer flag
        bool, typer.Option("--json", help="Print the numbers as JSON.")
    ] = False,
) -> None:
    """Print a run's numbers as markdown tables, each a query over its logs."""
    report = _run(lambda session: runs.report(session, run_id))
    typer.echo(report.model_dump_json(indent=2) if as_json else runs.report_markdown(report))


@app.command("export")
def export(
    out: Annotated[
        Path, typer.Option("--out", file_okay=False, help="The folder to write the files into.")
    ],
    since: Annotated[
        datetime | None,
        typer.Option(
            formats=["%Y-%m-%d"],
            show_default="today minus five years",
            help="Leave out documents dated before this day, and their records.",
        ),
    ] = None,
) -> None:
    """Write the records as JSON Lines, one file per record type, with documents.jsonl,
    citations.jsonl and manifest.json."""
    cutoff: date | None = None if since is None else since.date()
    manifest = _run(lambda session: exports.export(session, out, since=cutoff))
    for name, count in manifest["files"].items():
        typer.echo(f"{count:>6}  {out / name}")
