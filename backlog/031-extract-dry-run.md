# 031: Dry-run an extractor on stored snapshots

Spec: docs/specification/ (sections 4 UC-006, 7 "Manual rerun", 9)
Depends on: 029

## What to build

`gov-mine extract --dry-run --source <id> --extractor <name>` runs an extractor over the stored snapshots of a source's documents and prints what would change, without writing anything.

## Acceptance criteria

- [ ] The command prints, per document, the extracted fields and how they differ from the current record.
- [ ] Afterwards there are no new extractions, records, record snapshots, citations or `ai_calls` rows.
- [ ] Run with a rule extractor, it makes no model call.
- [ ] An unknown source or extractor exits non-zero.
