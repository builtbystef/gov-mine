# 020: Turn classified pages into sources and documents

Spec: docs/specification/ (sections 5.5, 7 step 5)
Depends on: 019

## What to build

A page classified as a listing becomes a source with a revisit interval for its type. A page classified as a document becomes a document. Both belong to the institution of the run that found them, and the run page shows the sources found and the documents by type.

## Acceptance criteria

- [x] A `listing:press_releases` classification creates a `sources` row with `crawl_interval` 1 day; `listing:projects` and `listing:rfp` get 7 days; every other listing type gets 30 days. `next_crawl_at` is the fetch time plus the interval.
- [x] A `document:<type>` classification creates a `documents` row of that type with the page's title and `document_date` from the snapshot's `stated_date`.
- [x] A `none` classification creates neither.
- [x] Sources and documents belong to the run's institution; a document reached through a listing records that listing as `source_id`, and one reached otherwise has `source_id` empty.
- [x] Re-running the job for the same snapshot creates no duplicate source (unique webpage and type) or document (unique webpage).
- [ ] The run page lists the sources found, with type, interval and next crawl, and the number of documents by type.

## Out of scope

- Extraction of the documents (023). Browsing documents (021).

## Notes

- Intervals by type are a user decision and are not editable in phase 1.
