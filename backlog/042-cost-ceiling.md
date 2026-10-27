# 042: Stop paid work at the run's cost ceiling

Spec: docs/specification/ (sections 4 UC-001 and UC-008, 7 "Events", 13, 14 decision 33)
Depends on: 034, 039

## What to build

Each run has a model cost ceiling, `max_cost`, default USD 5. Once the run's ledger passes it, no more classification, model extraction or OCR is queued, while fetching, parsing and rule extraction go on. The run shows a warning.

## Acceptance criteria

- [ ] A new run's `settings.max_cost` is 5 unless set otherwise.
- [ ] Once a run's `ai_calls` cost exceeds `max_cost`, a newly parsed page is not queued for `classify.page`, and a document without a rule is not queued for model extraction.
- [ ] Past the ceiling, scanned PDF pages are not OCR'd, and their snapshot is `partial`.
- [ ] Past the ceiling, fetching, parsing and rule extraction continue, and the run ends `finished`.
- [ ] The report, the run page and the Runs list show a warning when a run's cost passed its ceiling; whether it did is a query, not a stored flag.
- [ ] A page skipped for the ceiling is classified on a later run only when its content changes.
