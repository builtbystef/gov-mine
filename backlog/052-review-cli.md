# 052: Review low-confidence items from the CLI

Spec: docs/specification/ (sections 4 UC-009, 5.6 "Review", 7 "Review", 9, 14 decision 17)
Depends on: 024

## What to build

The review queue is a query: classifications and extractions below their confidence thresholds that have no review decision yet. Reviewers approve or reject items from the CLI or the API, and decisions are append-only.

## Acceptance criteria

- [ ] `GET /review` and `gov-mine review list` return, oldest first, classifications with confidence below 0.7 and extractions with confidence below 1.0 (the share of verified citations) that have no review decision.
- [ ] `gov-mine review approve <id> --note "ok"` writes a `review_decisions` row with reviewer `cli`, and the item leaves the queue.
- [ ] `POST /review-decisions` with a reviewer name records a decision for a classification or an extraction; exactly one of the two ids must be set, otherwise 422.
- [ ] A second decision on the same item adds a row, and the latest counts.
- [ ] A rule extraction (all citations verified) never appears in the queue.

## Out of scope

- What a rejection hides (055).
