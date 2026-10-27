# 043: Run incrementally from due sources

Spec: docs/specification/ (sections 4 UC-002 and UC-010, 7 "Scheduled re-run" and step 7)
Depends on: 012, 020, 037

## What to build

`gov-mine run create <id> --incremental` revisits only what is due: the listing pages of sources whose `next_crawl_at` has passed, the documents under them, and sitemap URLs not seen before. New listing items become new documents, and an unchanged site costs only requests.

## Acceptance criteria

- [ ] An incremental run starts from due sources' listing pages, their known documents and unseen sitemap URLs, and doesn't fetch the homepage.
- [ ] A new link on a due listing page is fetched and becomes a new document.
- [ ] A source whose listing page was fetched has `next_crawl_at` advanced by its `crawl_interval`; a listing page that failed leaves it unchanged.
- [ ] Against unchanged saved pages, an incremental run writes no snapshots and makes no paid calls.
- [ ] A MERX tender with an award document is not revisited.
- [ ] If every due listing page ends `failed_*` with no snapshot, the run ends `failed` with the error in `crawl_runs.error`.
