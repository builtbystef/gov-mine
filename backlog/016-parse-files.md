# 016: Parse PDFs, office files and plain text

Spec: docs/specification/ (sections 4 UC-001, 5.4, 14 decision 37)
Depends on: 013

## What to build

Files are parsed into markdown per page with MarkItDown: a PDF one page at a time, a slide or a sheet as a page. csv and txt are read as text. Images are kept without text. A file that can't be parsed is marked failed with its error, and its bytes are kept.

## Acceptance criteria

- [x] A saved Parkdale Hub PDF of N pages produces N text objects, `text/<id>/1` to `text/<id>/N`, with `parser = pdf:markitdown@1` and status `ready`.
- [x] A pptx produces one page per slide and an xlsx one page per sheet; a docx produces its text.
- [x] A csv or txt file produces one page of its text.
- [x] An image snapshot has `text_status = none` and no text objects.
- [x] A corrupt PDF ends with `text_status = failed` and `text_error` holding the parser's message; its bytes stay in storage, and the fetch that wrote it stays `fetched`.

## Out of scope

- Scanned pages with no text layer (034).

## Notes

- A parse failure is a snapshot state, not a fetch outcome (user decision, decision 37). Parse failures are not retried.
