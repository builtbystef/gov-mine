# 023: Extract records with the model

Spec: docs/specification/ (sections 4 UC-001 step 5, 5.6, 7 step 6, 8 extractor port, 11)
Depends on: 020

## What to build

Each document whose type maps to a record type is extracted by the model into typed records. Each field has a citation (page and excerpt), records are upserted by document and key, and the call's cost goes to the ledger.

## Acceptance criteria

- [x] There are seven record types (`project`, `news_item`, `meeting`, `contact`, `rfp`, `grant`, `contract`) with the fields, key field and required identifying field from section 5.6. A draft missing its identifying field fails validation.
- [x] Document types map to record types as in section 5.6 (`staff_directory` → `contact`); a `budget`, `procurement_guidelines`, `youtube`, `project_material`, `annual_report` or `strategic_plan` document is not extracted.
- [x] Extracting a news document writes one `extractions` row (`extractor = model:news_item@1`, `fallback_reason = no_rule`), one `records` row, one `record_snapshots` row with the validated data, one `citations` row per field (page and excerpt), and an `ai_calls` row with purpose `extract` linked to the extraction.
- [x] A staff directory page listing three people yields three `contact` records, keyed by name.
- [x] Extracting the same document again after its text changed adds a record snapshot to the same record, not a new record.
- [x] A model call that fails is retried once on a transport error; a final failure leaves the error on the extraction row, with no records written.
- [x] `current_records` returns each record's latest snapshot data, and the run's `settings` record the extractor versions.

## Out of scope

- Verifying excerpts (024): citations are stored with `verified = false` until then.
- The change-detection rules (027), rule extractors (029), the date cutoff (028).

## Notes

- Pydantic AI over OpenRouter with `GOV_MINE_EXTRACT_MODEL` and `reasoning_effort` from settings. Use structured output with the record type's schema and no tools (prompt-injection guard, section 11).
- The extractor name includes the model, as in section 8.
- Enable `pg_trgm` in this migration (section 5.8).
