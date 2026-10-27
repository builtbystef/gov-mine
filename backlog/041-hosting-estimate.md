# 041: Estimate the monthly hosting cost

Spec: docs/specification/13-deployment-and-operations.md (hosting cost estimate)
Depends on: 039

## What to build

The run report adds an estimated monthly cost of hosting gov-mine on Railway, clearly labelled as an estimate. It is computed from a hosting price list in code, the database's size and the snapshots' total `size_bytes`.

## Acceptance criteria

- [ ] A hosting price list in code holds Railway's prices and the assumed average use per service from section 13, with the date they were checked (2026-10-27).
- [ ] With a 1 GB database and 10 GB of snapshots, the estimate is memory 15 + CPU 5 + PostgreSQL volume 0.15 + bucket 0.15, about USD 20.30 a month.
- [ ] The storage figures come from `pg_database_size` and the sum of `webpage_snapshots.size_bytes`.
- [ ] The CLI report, the API report and the run page show the estimate labelled "estimate", separate from the actual model cost.
