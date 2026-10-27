# 024: Verify model citations with the quote check

Spec: docs/specification/ (sections 5.6, 7 "Quote check", 14 decision 6)
Depends on: 023

## What to build

Every citation from a model extraction is checked against the stored text of its page, and its `verified` flag says whether the excerpt is really there.

## Acceptance criteria

- [ ] An excerpt that appears on the cited page, differing only in case, whitespace, typographic quotes or dashes, or markdown syntax, is `verified = true`.
- [ ] An excerpt that is not on the cited page, or appears only on another page of the same snapshot, is `verified = false`.
- [ ] An excerpt shorter than twelve characters is `verified = false`.
- [ ] A match must fall on word boundaries: "port" inside "important" doesn't verify.
- [ ] An excerpt that only matches once all whitespace is removed (a line break inside a word in a PDF) is `verified = true`.

## Notes

- Copy Public Atlas's check from `../public-atlas/apps/server/src/public_atlas/modules/evidence/quote_checks.py`, adapted to read `text/<snapshot>/<page>`. Use the same markdown normaliser as `text_hash` (015).
- The extractor never sets `verified`.
