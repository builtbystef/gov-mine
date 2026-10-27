# 003: Tag log lines with run, job and webpage ids

Spec: docs/specification/10-cross-cutting-concerns.md
Depends on: 002

## What to build

Every log line a job writes carries the run id, the job id and, where there is one, the webpage id, so one run's or one page's activity can be filtered out of the logs.

## Acceptance criteria

- [x] A log line written during a `crawl.fetch` job, in JSON format, has `run_id`, `job_id` and `webpage_id` fields matching the job.
- [x] A log line written during a job that has no webpage (such as `crawl.start`) has `run_id` and `job_id`, and no `webpage_id`.
- [x] A log line written outside any job carries none of the three fields.

## Notes

- Use Alloy's existing JSON logging with context variables. Logfire stays off unless `GOV_MINE_LOGFIRE_TOKEN` is set.
