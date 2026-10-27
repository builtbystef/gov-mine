# 011: Handle failed requests

Spec: docs/specification/ (sections 4 UC-001 and UC-007, 5.4, 7 steps 2 and 7, 14 decision 28)
Depends on: 004

## What to build

Transient failures are retried within the run, other HTTP errors are recorded once, 404s mark the page missing, and a run whose homepage can't be fetched fails with its error shown on the run page.

## Acceptance criteria

- [x] A request that times out is retried up to three times with exponential backoff; each try is its own `fetches` row (`failed_timeout`), so a URL that never answers has four rows.
- [x] A 429 or 5xx is retried the same way, each try a `failed_http` row with its status; a retry that succeeds ends with a `fetched` row.
- [x] Any other 4xx writes one `failed_http` row and is not retried.
- [x] A 404 sets the webpage's `missing_since`; a later 200 for the same URL clears it.
- [ ] A full run whose homepage ends `failed_*` with no snapshot ends `failed`, with the error in `crawl_runs.error`, shown on the run page. (API side done: the run ends `failed` and `GET /runs/{id}` returns `error`; the run page itself is not checked yet.)
- [x] A failure on any other page doesn't stop the run, which ends `finished`.

## Out of scope

- The incremental-run failure rule (043).

## Notes

- One fetch row per try is a user decision (decision 28).
