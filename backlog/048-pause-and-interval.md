# 048: Pause an institution and set its full-crawl interval

Spec: docs/specification/ (sections 4 UC-008, 5.3, 7 "Scheduler")
Depends on: 044, 045

## What to build

The operator can pause or resume an institution and change how often it is fully re-crawled, from the dashboard.

## Acceptance criteria

- [ ] The Institutions list has a paused toggle that calls `PATCH /institutions/{id}`; after pausing, the scheduler creates no runs for that institution.
- [ ] Resuming lets the next tick create its due runs again.
- [ ] The edit form sets `full_crawl_interval` in days, and the institution page shows the new value.
- [ ] A changed interval changes when the scheduler next creates a full run.
