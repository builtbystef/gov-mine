# 013: Parse HTML snapshots to markdown

Spec: docs/specification/ (sections 5.4, 7 step 4, 8 `ingest.text` and the parser port, 9)
Depends on: 002

## What to build

Every new HTML snapshot is parsed into one markdown text by a parse job. The snapshot page in the dashboard shows that markdown and offers the raw file for download.

## Acceptance criteria

- [x] A new HTML snapshot enqueues `ingest.parse`, which writes `text/<snapshot id>/1`, sets `parser = html:compact@1` and moves `text_status` from `parsing` to `ready`.
- [x] The markdown of the saved CreateTO homepage keeps headings, body text, lists, tables and links with their hrefs, and contains no script, style, SVG, navigation or footer content.
- [x] `ingest.text(snapshot, page)` returns the markdown; it raises `TextNotReady` while the status is `parsing` and `NoText` when it is `none` or `failed`.
- [x] `GET /snapshots/{id}/text/{page}` returns the markdown, and `GET /snapshots/{id}/bytes` returns the raw bytes with the snapshot's media type.
- [ ] The dashboard's snapshot page shows the markdown per page and a link that downloads the raw file. (Not done: API side only, skipped under the time limit.)

## Notes

- HTML to markdown uses markdownify, the converter MarkItDown uses, so pages and files read alike; compaction uses selectolax.
- The parser is a pure function behind the parser port (section 8), returning pages, parser name and stated date (the date comes in 017).
