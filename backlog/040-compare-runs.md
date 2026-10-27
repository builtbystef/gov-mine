# 040: Compare two runs

Spec: docs/specification/04-use-cases.md (UC-003)
Depends on: 039

## What to build

`gov-mine run report <a> <b>` prints two runs' reports side by side, so a first run and an unchanged repeat can be compared in the README.

## Acceptance criteria

- [ ] The command prints one markdown table with a column per run and a row per number in the single-run report.
- [ ] An unchanged repeat of a run shows zero snapshots written and zero paid calls in its column.
- [ ] An unknown run id exits non-zero.
