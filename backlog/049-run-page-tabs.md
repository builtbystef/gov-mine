# 049: Explore a run through its tabs

Spec: docs/specification/ (sections 4 UC-007 step 3, 9 Runs)
Depends on: 025

## What to build

The run page gets tabs for the run's fetches, snapshots written, documents found or changed, and records created or amended.

## Acceptance criteria

- [ ] The Fetches tab filters by outcome and searches by URL, with both filters in the URL; `GET /runs/{id}/fetches` takes `outcome` and `q`.
- [ ] The Snapshots tab lists the snapshots the run wrote, each linked to its snapshot page.
- [ ] The Documents tab lists documents the run created or gave a new version, by type.
- [ ] The Records tab lists records the run created or amended, by type, each linked to its record page.
- [ ] Every tab is a server-paginated table.
