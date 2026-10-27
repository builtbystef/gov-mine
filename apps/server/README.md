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
│   ├── cli.py            # `gov-mine`, the command line
│   ├── config.py         # Settings; every GOV_MINE_* variable is documented in .env.example
│   ├── resources.py      # what every process opens once: database, store, queue, HTTP client
│   ├── modules/          # one package per feature: health, institutions, crawl, ingest, runs (the rest per docs/specification/06-architecture.md)
│   │   └── <feature>/    # router.py, schemas.py, models.py, service.py, jobs.py
│   ├── integrations/     # ports with their adapters: storage, ai, http (the crawler's client)
│   ├── jobs/             # the worker, the task registry, and platform tasks (stalled)
│   ├── db/               # declarative base, checked strings, session, and models.py, which imports every model
│   └── shared/           # AppError and subclasses, middleware, logs, telemetry, URL normalising, link finding and sitemap reading
├── alembic/              # migrations
└── tests/
    ├── unit/
    └── integration/      # real PostgreSQL, one rolled-back transaction per test
```

## Rules the code relies on

- **One place for the work.** A module's `service.py` does the work and raises `AppError`s. Routes, the CLI, and the worker's jobs all call the same service functions; none holds logic of its own.
- **No repository layer.** Services take the session; the session is the unit of work.
- **Narrow imports between modules.** A module imports another only through its `service`, `models`, `schemas`, and `dependencies`. Helpers with no feature of their own go in `shared/`.
- **The environment is read at the entry points.** Only `asgi.py` and `cli.py` read it. Everything else, tests included, receives a `Settings`.
- **Jobs commit with their data.** A job is queued on the handler's session, so it commits or rolls back with the rows it is about.
- **Tests never call the model.** The test settings drop the OpenAI key.

## Adding things

- **A model**: import its module in `db/models.py` so Alembic sees it, then add a migration: `uv run alembic revision --autogenerate -m "..."` from `apps/server`. CI fails on a model without a migration. An enumeration is a checked string (`db/checked_strings.py`): autogenerate writes it as a `CheckedString()` column without its constraint, so write it with a `checked()` helper as `alembic/versions/2026_10_27_0811-eb3ad4f1d8e7_crawl_the_homepage.py` does.
- **A route, or a change to request or response shapes**: run `vp run generate` from the root to regenerate the typed client.
- **A job**: put it in a `jobs.py` next to what it works on, register it with `task()`, and list the module in `TASK_MODULES` in `jobs/__init__.py`.
- **A setting**: add it to `Settings` and document it in `.env.example`.
- **A Procrastinate upgrade**: if the new version ships SQL migrations (`procrastinate/sql/migrations/` in the package), add an Alembic migration that runs them. `alembic/env.py` leaves the `procrastinate_*` tables out of autogenerate.

## How it works

- **Errors and logs**: every response and log line carries `X-Request-ID`. A line written inside a job also carries `job_id`, and the `run_id` and `webpage_id` the job was queued with (`LOGGED_ARGUMENTS` in `jobs/tasks.py`), as JSON fields with `GOV_MINE_LOG_FORMAT=json`. Unhandled exceptions become a plain 500.
- **Database**: SQLAlchemy 2 async over psycopg 3, migrations with Alembic.
- **Storage**: S3-compatible (RustFS locally); downloads use presigned URLs.
- **Jobs**: [Procrastinate](https://procrastinate.readthedocs.io) on the app's PostgreSQL, with no broker.
- **Runs**: `gov-mine run create` queues `crawl.start`, which reads the host's `/sitemap.xml` (and the sitemap files an index points to on that host), queues a fetch at depth 0 for the homepage and every URL listed, and queues `crawl.finish`. Reading the sitemap writes no `fetches` row and does not count toward `--limit`. A fetched HTML page queues a fetch one link deeper for every URL in it (`<a href>` and any absolute URL in the raw HTML) that the run has not queued yet; the fence in `crawl.fetch` refuses what is outside the institution's website prefix or more than 50 links deep with a `fetches` row and no request. `--limit N` caps the requests a run sends; the run's advisory lock makes the count and the queueing safe across concurrent fetches. Every job of a run carries `run_id`; `crawl.finish` marks the run finished once no other job with that `run_id` is waiting or running in `procrastinate_jobs`, and looks again every few seconds until then.
- **Models**: [Pydantic AI](https://pydantic.dev/docs/ai/), turned on by `GOV_MINE_OPENAI_API_KEY`. Every model call is recorded in `model_calls`.
