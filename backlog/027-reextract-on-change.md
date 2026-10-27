# 027: Re-extract only changed documents

Spec: docs/specification/ (sections 4 UC-002, 5.6, 7 step 6, 14 decision 23)
Depends on: 015, 023

## What to build

A snapshot is never extracted twice by the same extractor. The model reruns on a document only when its text changed. A record gets a new snapshot only when its data changed.

## Acceptance criteria

- [ ] Running `extract.document` twice for the same snapshot and extractor writes one extraction and makes one model call.
- [ ] A new snapshot with the same `text_hash` as the previous one (bytes changed, text didn't) gets no model extraction and no model call.
- [ ] A new snapshot with a different `text_hash` is extracted by the model again.
- [ ] A re-extraction that returns the same values writes an extraction and no new record snapshot.
- [ ] A re-extraction where one field changed writes one new record snapshot for that record only.
- [ ] A record a later extraction no longer mentions keeps its last state.

## Notes

- Removing records a page stops mentioning is out of scope in phase 1 (decision 19).
