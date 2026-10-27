# 057: Check health

Spec: docs/specification/13-deployment-and-operations.md (monitoring)
Depends on: 018

## What to build

`gov-mine health` checks that the database, object storage and OpenRouter can be reached, and says which one can't.

## Acceptance criteria

- [ ] With everything up, the command prints each check as OK and exits 0.
- [ ] With the database down, it reports the database as failing and exits non-zero; the other checks still run.
- [ ] With storage unreachable or no OpenRouter key, it reports that check as failing and exits non-zero.
- [ ] `--json` prints the same results as JSON.
