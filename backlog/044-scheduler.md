# 044: Schedule runs automatically

Spec: docs/specification/ (sections 4 UC-008, 7 "Scheduler", 14 decision 14)
Depends on: 038, 043

## What to build

A Procrastinate periodic task, `scheduler.tick`, runs every minute in the worker. It creates an incremental run for each institution with a due source, and a full run for each institution whose last full run is older than its full-crawl interval.

## Acceptance criteria

- [ ] An institution with a source whose `next_crawl_at` has passed gets one incremental run with `settings.trigger = scheduled`.
- [ ] An institution whose last finished full run is older than its `full_crawl_interval` (default 30 days), or which has never had one, gets one full run with `trigger = scheduled`.
- [ ] An institution with a `queued` or `running` run gets no new run.
- [ ] A paused institution gets no run.
- [ ] With two workers running, one tick creates each run only once.
- [ ] An error in a tick is logged, and the next tick runs normally.

## Notes

- The scheduler runs inside `gov-mine worker`, so `vp run dev` already starts it.
