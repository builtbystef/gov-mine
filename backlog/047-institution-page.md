# 047: Show an institution's page

Spec: docs/specification/09-external-interfaces.md (Institutions)
Depends on: 025, 045

## What to build

Each institution has a page showing its sources, documents by type, records by type, and runs.

## Acceptance criteria

- [ ] The page lists the institution's sources with type, interval, next crawl and extractor.
- [ ] It shows the number of documents and records per type, each linked to the list filtered to that institution and type.
- [ ] It lists the institution's runs, newest first, linked to their run pages.
- [ ] An unknown institution id shows a not-found page.
