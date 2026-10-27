# 035: Follow MERX search pages as a platform

Spec: docs/specification/ (sections 3, 4 UC-010 steps 1–2, 5.4, 5.6 "Platform rules", 7 step 3, 14 decision 24)
Depends on: 006, 008, 020

## What to build

`www.merx.com` is a `platform` host, because a platform rule (`rule:merx@1`) in code is keyed to it. From CreateTO's Procurement page, the crawler follows only URLs the rule's patterns match. The search becomes a `listing:rfp` source without the classifier, and the rule expands it into its open, closed and awarded tabs and their pages.

## Acceptance criteria

- [ ] The first link to `www.merx.com` creates its domain with policy `platform`, not `files_only`.
- [ ] The Procurement page's link to the MERX `createto` search is fetched, and becomes a `listing:rfp` source of the run's institution with no classification row.
- [ ] The rule enqueues the open, closed and awarded tabs with the same keywords, and every `pageNumber` page each tab links to.
- [ ] Links on MERX pages that match no pattern (login-gated `/public/supplier/interception/...` notices, document and plan-holder panels) get `skipped_scope` and no request.
- [ ] MERX requests are at least 5 s apart (its robots.txt `Crawl-delay`).
- [ ] Against the saved MERX fixtures, walking the three tabs reaches 108 distinct tender URLs.

## Out of scope

- Reading tenders (036) and awards (037).

## Notes

- Repeated rows in MERX's pagination mean some tenders are never reached; that is accepted for phase 1 (decision 34).
