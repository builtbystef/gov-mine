# apps/server

The FastAPI app and the Procrastinate worker (Python package `gov_mine`, distribution `gov-mine-server`).

```sh
vp run dev:api       # from the repo root, http://127.0.0.1:8000/docs
vp run dev:worker    # the job worker, restarted on changes
```

```text
apps/server/
├── src/gov_mine/
│   ├── asgi.py           # entry point for `fastapi run`/`fastapi dev`
│   ├── main.py           # create_app(settings): the API and its lifespan
│   ├── config.py         # Settings; every GOV_MINE_* variable is documented in .env.example
│   ├── resources.py      # what every process opens once: database, store, queue
│   ├── modules/          # one package per feature: health (the rest per docs/specification/06-architecture.md)
│   │   └── <feature>/    # router.py, schemas.py, models.py, service.py, jobs.py
│   ├── integrations/     # ports with their adapters: storage, ai
│   ├── jobs/             # the worker, the task registry, and platform tasks (stalled)
│   ├── db/               # declarative base, session, and models.py, which imports every model
│   └── shared/           # AppError and subclasses, middleware, logs, telemetry
├── alembic/              # migrations
└── tests/
    ├── unit/
    └── integration/      # real PostgreSQL, one rolled-back transaction per test
```

## Rules the code relies on

- **One place for the work.** A module's `service.py` does the work and raises `AppError`s. Routes, the CLI, and the worker's jobs all call the same service functions; none holds logic of its own.
- **No repository layer.** Services take the session; the session is the unit of work.
- **Narrow imports between modules.** A module imports another only through its `service`, `models`, `schemas`, and `dependencies`. Helpers with no feature of their own go in `shared/`.
- **The environment is read at the entry points.** Only `asgi.py` and `jobs/worker.py` read it. Everything else, tests included, receives a `Settings`.
- **Jobs commit with their data.** A job is queued on the handler's session, so it commits or rolls back with the rows it is about.
- **Tests never call the model.** The test settings drop the OpenAI key.

## Adding things

- **A model**: import its module in `db/models.py` so Alembic sees it, then add a migration: `uv run alembic revision --autogenerate -m "..."` from `apps/server`. CI fails on a model without a migration.
- **A route, or a change to request or response shapes**: run `vp run generate` from the root to regenerate the typed client.
- **A job**: put it in a `jobs.py` next to what it works on, register it with `task()`, and list the module in `TASK_MODULES` in `jobs/__init__.py`.
- **A setting**: add it to `Settings` and document it in `.env.example`.
- **A Procrastinate upgrade**: if the new version ships SQL migrations (`procrastinate/sql/migrations/` in the package), add an Alembic migration that runs them. `alembic/env.py` leaves the `procrastinate_*` tables out of autogenerate.

## How it works

- **Errors and logs**: every response and log line carries `X-Request-ID`. Unhandled exceptions become a plain 500.
- **Database**: SQLAlchemy 2 async over psycopg 3, migrations with Alembic.
- **Storage**: S3-compatible (RustFS locally); downloads use presigned URLs.
- **Jobs**: [Procrastinate](https://procrastinate.readthedocs.io) on the app's PostgreSQL, with no broker.
- **Models**: [Pydantic AI](https://pydantic.dev/docs/ai/), turned on by `GOV_MINE_OPENAI_API_KEY`. Every model call is recorded in `model_calls`.
