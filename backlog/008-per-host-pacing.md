# 008: Pace requests per host

Spec: docs/specification/ (sections 3, 7 step 2, 14 decision 15)
Depends on: 007

## What to build

A host is fetched one request at a time, and each request waits until the host's delay has passed since its last request, however many workers are running.

## Acceptance criteria

- [ ] With a worker concurrency of 4 and many URLs on one host, no two requests to that host overlap in time.
- [ ] Consecutive requests to one host start at least `crawl_delay_ms` apart (1 s by default, 5 s for a host whose robots.txt asks for 5).
- [ ] Requests to two different hosts can run at the same time.

## Notes

- Use a Procrastinate job `lock` keyed by domain id, not a hand-rolled advisory lock (decision 15).
