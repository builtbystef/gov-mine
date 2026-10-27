# 015: Compute a text hash that ignores nonces

Spec: docs/specification/ (sections 5.4, 10, 14 decision 23)
Depends on: 013

## What to build

Each parsed snapshot gets a `text_hash` that changes when its text or its links change, and not when only nonces, timestamps or build asset URLs change.

## Acceptance criteria

- [ ] `text_hash` is set when a snapshot is parsed, computed from its normalised markdown plus the sorted, normalised list of page and file links found anywhere in the raw content.
- [ ] Two copies of the saved CreateTO homepage that differ only in nonces and `/_next/static/<build id>/` asset URLs have the same `text_hash` and different content hashes.
- [ ] A copy with one PDF link added only inside `__NEXT_DATA__` has a different `text_hash`.
- [ ] A copy with one sentence of body text changed has a different `text_hash`.

## Notes

- The markdown normaliser used here is the same one the quote check uses (024); build it as one pure function.
- Link normalisation reuses the URL normaliser from 004.
