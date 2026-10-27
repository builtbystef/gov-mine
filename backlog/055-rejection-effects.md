# 055: Hide rejected items

Spec: docs/specification/ (sections 4 UC-009, 5.5, 5.6 "Review", 7 "Review")
Depends on: 043, 052, 054

## What to build

The latest review decision takes effect. A rejected classification stops its source being crawled and its document being extracted or exported. A rejected extraction's record snapshots drop out of current records and the export.

## Acceptance criteria

- [ ] A source whose classification was rejected is not seeded by incremental runs or the scheduler.
- [ ] A document whose classification was rejected is not extracted and is not in the export.
- [ ] After an extraction is rejected, `current_records` shows the record's previous snapshot, or no record if there is none, and the export follows.
- [ ] Approving an item changes nothing but the queue.
- [ ] Rejecting and then approving the same item restores it.
