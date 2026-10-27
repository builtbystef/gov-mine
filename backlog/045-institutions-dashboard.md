# 045: List and add institutions in the dashboard

Spec: docs/specification/ (sections 4 UC-007 step 1, 5.3, 9 Institutions)
Depends on: 002

## What to build

The dashboard lists institutions and lets the operator add or edit one by name, type and website. Saving makes the website's host a `crawl` domain.

## Acceptance criteria

- [ ] `GET /institutions` returns a limit/offset page; the Institutions list shows name, type, website, last run and next scheduled run.
- [ ] Submitting the Add form with a name, an `InstitutionType` and a website URL creates the institution through `POST /institutions` and shows it in the list.
- [ ] Saving an institution creates a `crawl` domain for its website's host, or sets an existing one to `crawl`.
- [ ] A website URL that isn't http or https, or a missing name, is refused with 422 and a message on the form.
- [ ] The Edit form changes an institution's name, type and location fields.

## Notes

- The next scheduled run shown is the earliest `next_crawl_at` of the institution's sources, or the date its full-crawl interval runs out, whichever comes first.
