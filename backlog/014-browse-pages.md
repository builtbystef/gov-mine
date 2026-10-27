# 014: Browse pages and their fetch history

Spec: docs/specification/09-external-interfaces.md (Pages; CLI `pages`)
Depends on: 013

## What to build

A webpage has a page in the dashboard showing its fetch history and snapshots, and the CLI can list and show webpages.

## Acceptance criteria

- [ ] `GET /webpages/{id}` returns the URL, its domain, `missing_since`, its fetches (newest first) and its snapshots.
- [ ] The dashboard's webpage page lists every fetch with run, time, outcome, HTTP status and reason, and every snapshot linked to its snapshot page.
- [ ] A fetch on the run page links to its webpage's page.
- [ ] `gov-mine pages list` prints webpages as a table, and `--json` prints the same rows as JSON.
- [ ] `gov-mine pages show <id>` prints the webpage with its fetches and snapshots; an unknown id exits non-zero.
