# 045: List and add institutions in the dashboard

Spec: docs/specification/ (sections 4 UC-007 step 1, 5.3, 9 Institutions)
Depends on: 002

## What to build

The dashboard lists institutions and lets the operator add or edit one by name, type and website. Saving makes the website's host a `crawl` domain.

## Acceptance criteria

- [x] `GET /institutions` returns a limit/offset page; the Institutions list shows name, type, website, last run and next scheduled run.
- [x] Submitting the Add form with a name, an `InstitutionType` and a website URL creates the institution through `POST /institutions` and shows it in the list.
- [x] Saving an institution creates a `crawl` domain for its website's host, or sets an existing one to `crawl`.
- [x] A website URL that isn't http or https, or a missing name, is refused with 422 and a message on the form.
- [x] The Edit form changes an institution's name, type and location fields.

## Notes

- The next scheduled run shown is the earliest `next_crawl_at` of the institution's sources, or the date its full-crawl interval runs out, whichever comes first.
- Sources do not exist yet, so the next scheduled run is the last run's start (or creation) plus the institution's full-crawl interval, and "Not scheduled" before its first run.
- Edit is `PUT /institutions/{id}` with the same body as Add.
