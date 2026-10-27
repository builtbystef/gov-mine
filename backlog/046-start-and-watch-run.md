# 046: Start a run from the dashboard and watch it

Spec: docs/specification/ (sections 4 UC-007 step 2, 9 Runs)
Depends on: 039, 045

## What to build

An institution has a Start full run button. The Runs list shows each run with live counts from the fetch log and its cost so far, refreshing every few seconds.

## Acceptance criteria

- [x] Clicking Start full run creates a run through `POST /runs` with `settings.trigger = dashboard`, and the Runs list shows it as `queued`.
- [x] Starting a run for an institution with an active run shows the 409 error, and no run is created.
- [ ] The Runs list shows institution, trigger, status, elapsed time, counts (fetched, not modified, skipped, blocked, failed), snapshots written, documents found, records extracted, and cost.
      All but documents found and records extracted, which wait for 019/020 and 023.
- [ ] While a run is running, the list and the run page refresh their counts every few seconds without a reload.
      Built (`refetchInterval` of 3 s while a run is queued or running), not watched live: no runs could be started on the shared dev database.
- [x] Every count comes from the API; the browser computes none.

## Decisions

- 039 (run report) is not built, so `GET /runs` and `GET /runs/{id}` carry `counts` from one grouped query on `fetches` (by outcome, plus snapshots written) and one on `ai_calls` (cost), and `elapsed_seconds`. `skipped` sums every `skipped_*`, `failed` every `failed_*`, and `not_modified` includes `unchanged`.
- The one-active-run rule (409) is in `runs.service.create_run`, so the CLI keeps it too.
