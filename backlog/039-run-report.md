# 039: Report a run

Spec: docs/specification/ (sections 2, 4 UC-001 step 6 and UC-003, 5.7, 13, 14 decision 9)
Depends on: 020, 023

## What to build

`gov-mine run report <id>`, `GET /runs/{id}/report` and the run page show a run's numbers. Every number is a query over the logs: nothing is counted by the crawler.

## Acceptance criteria

- [ ] The report gives elapsed time, requests by fetch outcome, files processed and failed (snapshots with `text_status = failed`), snapshots written, documents new and changed, records created and amended, paid calls by purpose, and cost by provider.
- [ ] It lists documents whose webpage went missing in the run (removed), documents left unextracted because their extraction failed, and `fallback_reason` counts per source.
- [ ] Against a seeded database with known rows, every number equals a hand count of those rows.
- [ ] `gov-mine run report <id>` prints the report as a markdown table; `--json` prints the same numbers as JSON.
- [ ] The run page shows the same report from `GET /runs/{id}/report`.

## Out of scope

- Comparing two runs (040), the hosting estimate (041), the cost-ceiling warning (042).

## Notes

- A request is a `fetches` row with a request sent, so retries count (decision 28). Model costs are the ledger's actual costs.
