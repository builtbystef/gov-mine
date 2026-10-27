# The API and the worker. One image; the deployment picks the command (see
# Deploying in the root README).
# Build from the repository root, where the uv workspace and lockfile live:
#
#   docker build --file apps/server/Dockerfile --tag gov-mine-server .

# --- Dependencies -------------------------------------------------------------
# The Python from .python-version, and uv copied in from its own image: the
# version must satisfy `required-version` in the root pyproject.toml.
FROM python:3.14-slim-bookworm AS build

COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first, from the lockfile alone, so this layer survives source
# changes. The workspace member's pyproject.toml is needed for the resolution.
COPY pyproject.toml uv.lock ./
COPY apps/server/pyproject.toml apps/server/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-workspace --package gov-mine-server

# Then the project itself: source, migrations, and the Alembic and FastAPI
# config in apps/server. An editable install, so the venv points at /app/apps/server.
COPY apps/server apps/server
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --package gov-mine-server

# --- Runtime ------------------------------------------------------------------
FROM python:3.14-slim-bookworm AS runtime

# Trust X-Forwarded-* from any peer: only the web app's proxy route can reach
# the API. Narrow this to the web service's network if the API is ever exposed
# more widely.
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    FORWARDED_ALLOW_IPS="*"

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY --from=build --chown=app:app /app /app

# `fastapi run` and `alembic` read pyproject.toml from the working directory.
WORKDIR /app/apps/server
USER app

EXPOSE 8000

# No HEALTHCHECK here: the worker runs from this image too and serves no HTTP,
# so an image-level check would mark it unhealthy for good.
# The deployment gives the `api` process one (see Deploying in the root README).

# No reload, binds 0.0.0.0.
CMD ["fastapi", "run", "--port", "8000", "--proxy-headers"]
