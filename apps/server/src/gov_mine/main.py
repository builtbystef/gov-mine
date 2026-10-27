"""The API. `create_app` builds it from a `Settings`; the lifespan opens the
resources once and puts them on `request.state` (dependencies.py reads them from
there)."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from gov_mine.config import Settings
from gov_mine.dependencies import SettingsDep
from gov_mine.modules.router import router as api_router
from gov_mine.resources import build_resources
from gov_mine.shared import logs, telemetry
from gov_mine.shared.exceptions import AppError, handle_app_error
from gov_mine.shared.middleware import RequestIdMiddleware
from gov_mine.shared.routing import generate_unique_id

if TYPE_CHECKING:
    import httpx
    import httpx2
    from procrastinate.connector import BaseConnector

    from gov_mine.integrations.storage import ObjectStore


def create_app(
    settings: Settings,
    *,
    object_store: ObjectStore | None = None,
    jobs_connector: BaseConnector | None = None,
    models_http: httpx.AsyncClient | None = None,
    extract_http: httpx2.AsyncClient | None = None,
) -> FastAPI:
    """The doubles go to `build_resources`; tests pass an in-memory store and an
    in-memory queue."""
    logs.configure(settings.log_level, settings.log_format)
    if (log_handler := telemetry.configure(settings, service_name="gov-mine-server")) is not None:
        logging.getLogger().addHandler(log_handler)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[dict[str, object]]:
        """The yielded dict becomes `request.state`."""
        async with build_resources(
            settings,
            object_store=object_store,
            jobs_connector=jobs_connector,
            models_http=models_http,
            extract_http=extract_http,
        ) as resources:
            yield {"resources": resources}

    app = FastAPI(
        title=settings.app_name,
        generate_unique_id_function=generate_unique_id,
        lifespan=lifespan,
    )
    if telemetry.enabled(settings):
        telemetry.instrument_app(app)
        telemetry.instrument_agents()
    # Inside the Logfire span, so the request ID reaches its logs. No CORS and no
    # body limit: browsers only reach the API through the Next.js proxy route,
    # which is same-origin and refuses large bodies itself.
    app.add_middleware(RequestIdMiddleware)
    app.add_exception_handler(AppError, handle_app_error)
    app.include_router(api_router)

    @app.get("/")
    async def read_root(settings: SettingsDep) -> dict[str, str]:
        return {"app": settings.app_name}

    return app
