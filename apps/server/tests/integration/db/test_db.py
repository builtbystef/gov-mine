import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import text

from gov_mine.db.base import include_name
from gov_mine.db.models import Base

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import AsyncEngine
    from tests.integration.conftest import Database

API_ROOT = Path(__file__).resolve().parents[3]


def test_health_db_without_override_uses_lifespan_engine(app: FastAPI):
    """The real `get_session`, not the test override."""
    with TestClient(app) as client:
        response = client.get("/health/db")
    assert response.status_code == 200


def _upgrade_and_compare(connection: Connection) -> list[object]:
    config = Config(file_=API_ROOT / "alembic.ini", toml_file=API_ROOT / "pyproject.toml")
    # env.py migrates on this connection instead of opening its own.
    config.attributes["connection"] = connection
    command.upgrade(config, "head")
    context = MigrationContext.configure(connection, opts={"include_name": include_name})
    diff = compare_metadata(context, Base.metadata)
    command.downgrade(config, "base")
    return diff


def test_migrations_match_models(engine: AsyncEngine):
    """Catches a model change without a migration, or a migration that drifted."""

    async def run() -> list[object]:
        async with engine.connect() as connection:
            await connection.begin()
            diff = await connection.run_sync(_upgrade_and_compare)
            await connection.rollback()
        await engine.dispose()
        return diff

    assert asyncio.run(run()) == []


PROBE = "SELECT to_regclass('public.rollback_probe')"


def test_committed_writes_stay_inside_the_test_transaction(db: Database, engine: AsyncEngine):
    """A commit is a released savepoint: visible in the test, invisible outside."""

    async def create_probe_table() -> str | None:
        async with db.session() as session:
            await session.execute(text("CREATE TABLE rollback_probe (id integer)"))
            await session.commit()
            return (await session.execute(text(PROBE))).scalar_one()

    async def probe_from_a_new_connection() -> str | None:
        async with engine.connect() as connection:
            return (await connection.execute(text(PROBE))).scalar_one()

    assert db.run(create_probe_table) == "rollback_probe"
    assert asyncio.run(probe_from_a_new_connection()) is None
