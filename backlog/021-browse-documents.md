# 021: Browse documents

Spec: docs/specification/09-external-interfaces.md (Documents; CLI `documents list`)
Depends on: 020

## What to build

The dashboard lists documents and shows each one with its versions. The CLI lists documents.

## Acceptance criteria

- [ ] `GET /documents` returns a limit/offset page filterable by institution, type and date, and the dashboard's Documents list uses those filters, kept in the URL.
- [ ] `GET /documents/{id}` returns the document with its versions: the webpage's snapshots with distinct text hashes, newest first.
- [ ] The dashboard's document page shows title, type, date, URL, parent document if any, and its versions, each linked to its snapshot page.
- [ ] `gov-mine documents list --type projects --since 2024-01-01` prints only project documents dated on or after that day; `--json` prints the same rows as JSON.

## Out of scope

- The records extracted from a document (025).
