# 12. Development Guidelines

- Code organization: Alloy's layout. `apps/server/src/gov_mine/modules/` holds one package per
  module in section 6 (`institutions`, `crawl`, `ingest`, `classify`, `extract`, `ledger`,
  `review`, `runs`, `scheduler`, `jobs`), each with `models.py`, `service.py`, `jobs.py`,
  `router.py` and `schemas.py` as needed; `integrations/` holds one package per port, with
  `base.py` for the interface, one file per adapter and `memory.py` for the fake; then
  `cli.py`, `db/` and `jobs/` (worker and task registry). `apps/server/alembic/` holds the
  migrations and `apps/server/tests/` mirrors `src/`. `apps/server/fixtures/createto/` holds
  saved pages for tests and replay; `apps/server/fixtures/merx/` the same for MERX (search
  tabs, tender pages, award panels). The dashboard is `apps/web/`, one folder per feature
  under `src/features/`; the generated client is `packages/api-client/`. Each app keeps
  Alloy's README with its code map.
- Naming conventions: tables plural snake_case; enum values snake_case strings; job functions
  `module.verb_noun`; extractor and parser names `<kind>:<name>@<version>`.
- Formatting: Ruff format and lint and ty for Python; oxfmt, oxlint and tsc through `vp check`
  for TypeScript; the pre-commit hook (`vp config`) runs `vp staged`, which formats, lints and
  typechecks the staged files; CI runs the full `vp run check`.
- Function size and responsibility guidance: a job function orchestrates and writes rows; the
  logic it calls is pure where possible (fence decisions, URL normalisation, compaction, the
  quote check, cost computation) so it can be tested without a database.
- Testing conventions: pytest; unit tests for the pure functions with real saved pages as
  inputs; integration tests against a PostgreSQL in Docker with fake ports for HTTP and models;
  one end-to-end test that crawls the replay server and asserts the report.
- What must be covered by automated tests: the fence (every refusal reason); URL normalisation;
  snapshot idempotence; `text_hash` stability across nonces; the classifier input builder; the
  quote check; the extraction dedupe key; record upsert by document and key and
  snapshot-on-change; the review queue query and what a rejection hides; the document date
  rule and the date cutoff; the `platform` fence and the MERX rule on saved MERX pages; cost
  computation; the report queries against a seeded database.
- Code review expectations: solo project; the coding agent works from Alloy's `AGENTS.md` and
  ticket skills (`spec-to-tickets`, `implement-ticket`, `review-ticket`, `test-ticket`), and
  its changes are reviewed by the author before commit; `vp run check` and `vp run test` green
  before every commit; commits small and named by module.
