# 012: Re-fetch with conditional requests

Spec: docs/specification/ (sections 4 UC-002, 5.4, 7 step 3)
Depends on: 004

## What to build

A page fetched before is requested with the validators it last sent. A 304 or identical bytes cost one request and write no snapshot.

## Acceptance criteria

- [ ] After a 200 with `ETag` or `Last-Modified`, the webpage row stores `etag` and `last_modified`.
- [ ] The next request for that URL sends `If-None-Match` and `If-Modified-Since` with the stored values.
- [ ] A 304 response writes a `not_modified` fetch and no snapshot.
- [ ] A 200 whose bytes hash to the webpage's existing content hash writes an `unchanged` fetch, with `snapshot_id` empty, and no snapshot.
- [ ] Running a full crawl twice against unchanged saved pages writes snapshots only on the first run.
