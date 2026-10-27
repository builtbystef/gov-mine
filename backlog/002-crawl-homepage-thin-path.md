# 002: Crawl CreateTO's homepage and show it on the run page

Spec: docs/specification/ (sections 4 UC-001, 5.3, 5.4, 5.7, 7, 9)
Depends on: 001

## What to build

The thinnest path through the system. `gov-mine seed` creates the CreateTO institution. `gov-mine run create <institution id> --full` queues a run that fetches the homepage, stores the bytes as a snapshot and finishes. The dashboard's Runs list and run page show the run, its fetch and the snapshot.

## Acceptance criteria

- [x] `gov-mine seed` creates one CreateTO institution (`municipal_agency`, website `https://createto.ca/`) and a `crawl` domain for its host; running it again creates nothing new.
- [x] `gov-mine run create <id> --full` prints the new run's id; the run is `queued` with `settings.trigger = cli` and `settings` marking it full.
- [x] With a worker running, the run becomes `running`, then `finished`, with `started_at` and `finished_at` set.
- [x] The run has exactly one `fetches` row for the homepage, with outcome `fetched`, its HTTP status, duration and `snapshot_id`.
- [x] The snapshot's bytes are in object storage at `bytes/<snapshot id>`, and its row has the content hash, media type and `size_bytes` equal to the stored length.
- [x] `GET /runs` and `GET /runs/{id}/fetches` return limit/offset pages (`{items, total, limit, offset}`); the dashboard's Runs list shows the run and its status, and the run page lists the homepage fetch with its outcome and snapshot.
- [x] `run create` with an unknown institution id exits non-zero and creates no run.

## Out of scope

- Following links (004), robots and pacing (007, 008), parsing (013).
- Live counts and the Start button in the dashboard (046).
- Run status and cancel commands (038).

## Notes

- `crawl.finish` marks the run finished when no job carrying its `run_id` is left waiting or running. Build that real mechanism here, not a "finish after the homepage" shortcut.
- Store the bytes before inserting the snapshot row: an orphan object is harmless, an orphan row is not (section 10).
- Status and outcome columns are checked strings. Copy Public Atlas's checked-string enum helper here, from `../public-atlas/apps/server/src/public_atlas/`. Add the index on `fetches (crawl_run_id, outcome)`.
- Tables created here: `institutions` (with `full_crawl_interval` and `paused`), `domains`, `webpages`, `fetches`, `webpage_snapshots` and `crawl_runs`, with the columns from section 5. Each needs an Alembic migration.
