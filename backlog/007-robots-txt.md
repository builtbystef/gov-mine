# 007: Honour robots.txt

Spec: docs/specification/ (sections 3, 5.4, 9 "Crawler identity")
Depends on: 004

## What to build

The crawler fetches each host's robots.txt once and caches it on the domain. URLs it disallows are logged as `blocked_robots` and never requested. Every request identifies the crawler as `my-bot/<version>`.

## Acceptance criteria

- [x] The first URL on a host fetches its robots.txt; the domain row stores `robots_txt` and `robots_fetched_at`, and later URLs on that host in the run don't fetch it again.
- [x] A URL disallowed for `*` or for `my-bot` gets a `blocked_robots` fetch and no request.
- [x] Every request sends the `User-Agent` `my-bot/<version>`.
- [x] A host's `Crawl-delay` is stored as `crawl_delay_ms` when it is longer than the 1 s default; otherwise `crawl_delay_ms` is 1000. Saved MERX robots.txt gives 5000.
- [x] A host whose robots.txt returns 404 allows every path.

## Notes

- `my-bot` is a placeholder with no contact yet (user decision).
