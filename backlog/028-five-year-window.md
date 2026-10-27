# 028: Apply the five-year window

Spec: docs/specification/ (sections 3, 5.5, 7 steps 5–6, 14 decisions 18 and 29)
Depends on: 017, 023

## What to build

Each run records its cutoff, its start date minus five years. A document's date is the latest date it states about itself. Documents dated before the cutoff are kept and not extracted.

## Acceptance criteria

- [ ] A run started on 2026-10-27 has `settings.cutoff = 2021-10-27`.
- [ ] A document whose snapshot's `stated_date` is 2019-06-01 is not queued for extraction and has no extraction.
- [ ] A project first published in 2019 and updated in 2024 (stated date 2024) is extracted.
- [ ] A document with no stated date is extracted; if the extractor reads a publication date in the text, it becomes the document's `document_date`.
- [ ] A new snapshot with a later `stated_date` updates `document_date`, and the document is then extracted if it is within the window.

## Notes

- The rolling window is a user decision (decision 29).
