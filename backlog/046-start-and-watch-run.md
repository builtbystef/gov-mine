# 046: Start a run from the dashboard and watch it

Spec: docs/specification/ (sections 4 UC-007 step 2, 9 Runs)
Depends on: 039, 045

## What to build

An institution has a Start full run button. The Runs list shows each run with live counts from the fetch log and its cost so far, refreshing every few seconds.

## Acceptance criteria

- [ ] Clicking Start full run creates a run through `POST /runs` with `settings.trigger = dashboard`, and the Runs list shows it as `queued`.
- [ ] Starting a run for an institution with an active run shows the 409 error, and no run is created.
- [ ] The Runs list shows institution, trigger, status, elapsed time, counts (fetched, not modified, skipped, blocked, failed), snapshots written, documents found, records extracted, and cost.
- [ ] While a run is running, the list and the run page refresh their counts every few seconds without a reload.
- [ ] Every count comes from the API; the browser computes none.
