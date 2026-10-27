# 036: Read MERX tenders into rfp records

Spec: docs/specification/ (sections 4 UC-010 step 3, 5.6)
Depends on: 023, 035

## What to build

Each MERX tender page becomes an `rfp` document of the institution, which the MERX rule reads into an `rfp` record from its labelled fields, without a model.

## Acceptance criteria

- [ ] A saved CreateTO tender page becomes an `rfp` document, without the classifier, and an `rfp` record with title, description, solicitation number, type, location, publication date, closing date and status read by `rule:merx@1`.
- [ ] Every field's citation is the raw labelled value, `verified = true`, and no `ai_calls` row is written.
- [ ] A tender whose Issuing Organization doesn't contain the institution's name keeps its snapshot and yields no document.
- [ ] A tender page missing its title fails validation and falls back to the model with `fallback_reason = validation_failed`.
- [ ] The tender's `document_date` is its publication date as read by the rule.

## Notes

- MERX gives no NAICS code or value, so those stay empty.
