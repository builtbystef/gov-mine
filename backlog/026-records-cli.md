# 026: Inspect records from the CLI

Spec: docs/specification/09-external-interfaces.md (CLI `records`)
Depends on: 023

## What to build

The CLI lists records of a type, shows one record with its citations, and prints its history.

## Acceptance criteria

- [ ] `gov-mine records list --type project` prints current project records as a table; `--json` prints the same as JSON.
- [ ] `gov-mine records show <id>` prints each field with its citation (URL, page, excerpt, verified).
- [ ] `gov-mine records history <id>` prints each record snapshot, oldest first, with the fields that changed and the extraction and run that produced it.
- [ ] An unknown id exits non-zero.
