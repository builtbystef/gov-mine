# 025: Browse records and citations in the dashboard

Spec: docs/specification/ (sections 4 UC-007 step 4, 9 Records)
Depends on: 021, 024

## What to build

The dashboard lists records by type and shows each record with its fields, the citation behind each field, and its history.

## Acceptance criteria

- [x] `GET /records?type=project` returns a limit/offset page of current project records; the Records list shows the type's fields as columns, with the type filter in the URL.
- [x] `GET /records/{id}` returns the record's current fields, each with its citation (URL, page, excerpt, verified), and its record snapshots, newest first.
- [x] On the record page each field shows its excerpt and verified flag, and links to the snapshot page with the excerpt highlighted.
- [x] The record page shows its history, each record snapshot as a diff of changed fields against the previous one.
- [ ] The document page lists the records extracted from the document.
