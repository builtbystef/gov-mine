# 054: Export records as JSON Lines

Spec: docs/specification/ (sections 4 UC-005, 9 "Export files")
Depends on: 028

## What to build

`gov-mine export [--since <date>] --out <dir>` writes one JSON Lines file per record type, one for documents and one for citations, plus a manifest.

## Acceptance criteria

- [ ] The output directory holds `projects.jsonl`, `news_items.jsonl`, `meetings.jsonl`, `contacts.jsonl`, `rfps.jsonl`, `grants.jsonl`, `contracts.jsonl`, `documents.jsonl`, `citations.jsonl` and `manifest.json`.
- [ ] Each record line has `id`, `institution`, `document` (its URL), `key`, the typed fields, `citations` (`field`, `url`, `page`, `excerpt`, `verified`), `first_seen_at` and `last_changed_at`.
- [ ] Each document line has `id`, `institution`, `url`, `document_type`, `title`, `document_date`, `parent` (the parent's URL) and `first_seen_at`.
- [ ] Without `--since`, documents dated before today minus five years, and their records, are left out; undated documents are kept. `--since 2024-01-01` moves the cutoff.
- [ ] `manifest.json` gives the export time, the cutoff, the latest finished run of each exported institution, the extractor versions and each file's line count.
- [ ] Exporting twice from the same database gives the same lines.
