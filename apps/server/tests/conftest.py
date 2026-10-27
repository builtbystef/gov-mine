"""The settings every test builds on. Nothing here touches the environment: the
configured server (environment or `.env`) is read once, and the tests get a copy
pointed at the test database."""

import os
from typing import TYPE_CHECKING

import pytest
from pydantic import PostgresDsn
from sqlalchemy.engine import make_url

from gov_mine.config import Settings

if TYPE_CHECKING:
    from sqlalchemy.engine import URL

# TEST_DATABASE_SUFFIX names the test databases apart, so test runs in two worktrees at once
# do not drop each other's.
TEST_DATABASE = "gov_mine_test" + os.environ.get("TEST_DATABASE_SUFFIX", "")

# The development server, as configured.
_configured = Settings()
_configured_url = make_url(str(_configured.database_url))
_test_url = _configured_url.set(database=TEST_DATABASE).render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def configured_url() -> URL:
    """The development server, for creating the test database."""
    return _configured_url


@pytest.fixture(scope="session")
def test_database_name() -> str:
    return TEST_DATABASE


@pytest.fixture
def settings() -> Settings:
    """The configured settings, on the test database. No OpenAI key, whatever a
    local `.env` says: tests never call the model. A module or class that needs
    other values overrides this fixture, requesting it as the base."""
    return _configured.model_copy(
        update={
            "database_url": PostgresDsn(_test_url),
            "app_name": "Test API",
            "openai_api_key": None,
        }
    )
