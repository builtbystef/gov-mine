# 032: Rerun an extractor by hand

Spec: docs/specification/ (sections 5.6, 7 "Manual rerun", 9, 14 decision 20)
Depends on: 027

## What to build

After an extractor's version is bumped, `gov-mine extract --rerun --extractor <name> [--institution <id>] [--type <record type>]` re-extracts the latest snapshot of every matching document that this extractor hasn't processed yet.

## Acceptance criteria

- [ ] For every matching document without an extraction of its latest snapshot by this extractor, an `extract.document` job is queued with no run id; the documents that already have one are skipped.
- [ ] The resulting extractions have `crawl_run_id` empty, and their model calls are in `ai_calls`.
- [ ] A rerun that finds the same values writes extractions and no record snapshots.
- [ ] `--institution` and `--type` limit which documents are rerun.
- [ ] `--rerun --dry-run` prints which documents would be queued and queues nothing.

## Notes

- Nothing reruns automatically when an extractor changes.
