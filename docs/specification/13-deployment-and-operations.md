# 13. Deployment and Operations

- Environments and hosting: local first: Docker Compose with PostgreSQL 18 and RustFS; the
  API, worker (with the scheduler) and CLI run from `uv run`; the dashboard from `pnpm dev`.
  For the demo the whole app is hosted on Railway, built from Alloy's Dockerfiles: services for
  web, API and worker, Railway PostgreSQL, and a Railway S3-compatible bucket. Only the web
  service has a public domain; the API is reached over Railway's private network. There is no
  login: the URL is unlisted and shared privately, and the project is deleted after the demo
  (decision 26). Alloy's image build (GitHub Actions,
  `.github/workflows/images.yml`) stays for CI.
- Hosting cost estimate: from the first run, the run report and the README give an estimated
  monthly cost of running gov-mine hosted on its schedule, labelled as an estimate: Railway's
  usage pricing for the web, API and worker services and PostgreSQL, and the bucket priced by
  the GB the snapshots take (read from the database). The prices are a hosting price list in
  code, next to the model price list, with the date they were checked. On 2026-10-27
  (railway.com/pricing): USD 20 per vCPU-month and 10 per GB-month of memory, billed per second
  on actual use; volumes 0.15 per GB-month; buckets 0.015 per GB-month with free egress;
  service egress 0.05 per GB; the Hobby plan USD 5 a month and Pro USD 20, each including that
  much usage. Railway bills use, not allocation, so the estimate assumes an average use per
  service, kept in the same price list: web and API 0.05 vCPU and 0.25 GB each, the worker 0.1
  vCPU and 0.5 GB, PostgreSQL 0.05 vCPU and 0.5 GB plus a volume the size of the database
  (`pg_database_size`); the bucket is the snapshots' total `size_bytes`. On those assumptions
  it is about USD 20 a month (memory 15, CPU 5, storage cents), before the plan's included
  usage.
- Build and deployment process: `uv sync`; `pnpm install`; `vp run db:up` (PostgreSQL and
  RustFS in Docker Compose); `vp run db:migrate`; `uv run gov-mine seed`; one command (`vp run
  dev`, as in Alloy) starts the API, a worker with the scheduler, and the dashboard.
  Dockerfiles build one image for API and worker and one for the dashboard.
- Database migrations: Alembic, one migration per change, autogenerate checked by hand; a test
  compares every check constraint with its enum.
- Monitoring and alerts: the run report and `run status`; structured logs (Logfire if a token is
  set); a `gov-mine health` command checks database, storage and provider reachability. No
  paging in phase 1. The template-drift signal is `fallback_reason` counts per source in the
  report.
- Backups and recovery: the database is the index and the object store holds the snapshots;
  `pg_dump` plus a bucket copy is a full backup. The snapshots can be re-parsed, re-classified
  and re-extracted from bytes alone, so losing derived tables is recoverable at model cost.
- Rollback approach: migrations are reversible; extractor and parser versions are additive, so
  rolling back code never invalidates stored rows.
- Operational responsibilities: the author. Cost ceiling: a per-run `max_cost` in settings,
  default USD 5, stops enqueuing paid jobs when the ledger for the run passes it.
