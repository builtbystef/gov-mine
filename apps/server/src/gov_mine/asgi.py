"""The ASGI entry point for `fastapi run` and `fastapi dev`: the one place, with
the CLI, where the API reads the environment. Everything else (tests, the
OpenAPI export) calls `create_app` with its own settings."""

from gov_mine.config import Settings
from gov_mine.main import create_app

app = create_app(Settings())
