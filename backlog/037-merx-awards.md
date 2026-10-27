# 037: Read MERX awards into contract records

Spec: docs/specification/ (sections 3, 4 UC-010 step 4, 5.6)
Depends on: 036

## What to build

An awarded tender's award panel is fetched from MERX's award URL, unwrapped from its jQuery response, and read into a `contract` record. The panel is a document belonging to its tender.

## Acceptance criteria

- [ ] An awarded tender enqueues `/public/solicitations/<id>/abstract/award`, requested with `X-Requested-With: XMLHttpRequest`.
- [ ] The panel becomes a document with `parent_document_id` set to the tender's document.
- [ ] The rule reads the saved panel into a `contract` record with `origin = award`: vendor name, vendor address, award date and total value.
- [ ] A panel whose value is "Undisclosed" gives a contract with `total_value` empty.
- [ ] Against the saved fixtures a full run gets 74 contract records and makes no model call.
