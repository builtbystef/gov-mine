# 034: OCR scanned PDF pages

Spec: docs/specification/05-data-model.md (section 5.4)
Depends on: 016, 018

## What to build

A PDF page with no text layer is read by MarkItDown's OCR plugin with `openai/gpt-6-luna` over OpenRouter, and each call is a paid call in the ledger.

## Acceptance criteria

- [ ] A PDF whose page 2 is a scan gets OCR text for page 2 at `text/<id>/2`, and status `ready`.
- [ ] Each OCR call writes an `ai_calls` row with purpose `ocr`, the run's id, and no classification or extraction id.
- [ ] A PDF with a text layer on every page makes no OCR call.

## Notes

- Use `markitdown-ocr` through a client wrapper that records the ledger row.
