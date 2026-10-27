# 4. Use Cases

## UC-001: First crawl of an institution

- Goal: keep a copy of every page and linked file of an institution's site and produce typed
  records with citations.
- Actors: Operator (the developer or reviewer, via CLI); the target website; the classifier and
  extractor model providers.
- Preconditions: the institution row exists with a `website_url`; PostgreSQL and object storage
  are running; a worker is running; model keys are configured.
- Main steps:
  1. Operator runs `gov-mine run create createto --full`.
  2. The run is queued; the worker fetches robots.txt and the sitemap for the host, then the
     homepage, and follows every in-scope link breadth-first, writing a `fetches` row per
     attempt and a `webpage_snapshots` row per new content hash.
  3. Each new snapshot is parsed to markdown per page (HTML compacted; PDF and office files via
     MarkItDown, scanned PDF pages via its LLM OCR plugin) as parse jobs.
  4. Each webpage is classified once, on its first parsed snapshot: none, listing of type X,
     or document of type X. Listings become `sources`; documents become `documents`. A file
     listed in a project's materials becomes a `project_material` document of that project
     without the classifier.
  5. Each document is extracted: the rule whose URL pattern matches its URL, if any, else the
     model. Records are upserted by document and key, a `record_snapshots` row written when
     data changed, and a `citations` row per field, model excerpts checked against the snapshot
     text.
  6. The run finishes; `gov-mine run report <id>` prints the numbers.
- Alternative flows, including failures:
  - robots.txt disallows a path: the link gets a `blocked_robots` fetch and no request.
  - A link is off-scope, an unsupported type, or too large: `skipped_*` fetch, no request.
  - A request times out or returns 5xx: `failed_http` or `failed_timeout`; retried up to three
    times with backoff within the run; the run continues.
  - A file cannot be parsed: snapshot `text_status = failed` with `text_error`; the fetch is
    `failed_parse`; the bytes are kept.
  - A model call fails: the extraction row records the error; retried once; the document stays
    unextracted and appears in the report.
  - The worker dies mid-run: within ten minutes of a worker restarting, the stalled-job sweep
    puts its unfinished jobs back in the queue; the run resumes.
- Expected result: a snapshot of every page and file, a few sources, a few hundred documents,
  typed records with verified citations, and a report.
- Business rules: never fetch a private address; never follow links on `files_only` hosts;
  on `platform` hosts follow only the URLs the platform rule's patterns match;
  never write a snapshot for unchanged bytes; never extract the same snapshot twice with the
  same extractor; never store a model citation that was not checked.

## UC-002: Scheduled re-run

- Goal: notice what changed since the last run at the lowest cost.
- Actors: the built-in scheduler (or the operator, from the dashboard or CLI); the target
  website.
- Preconditions: UC-001 has run at least once; sources have intervals.
- Main steps:
  1. The scheduler creates an incremental run for each institution with a source due.
  2. The worker revisits due sources' listing pages and the documents under them with
     conditional requests (`If-None-Match`, `If-Modified-Since`).
  3. `304` → `not_modified` fetch. `200` with the same content hash → `unchanged`. New content
     hash → a new snapshot; if the page is a document, its rule extractor (free) runs again,
     and the model only if `text_hash` also changed. Pages are not re-classified.
  4. Re-extraction produces a `record_snapshots` row only for records whose data changed.
  5. New listing items are fetched as new documents.
- Alternative flows: a document URL returns 404 → `webpages.missing_since` is set; the document
  is reported as removed. A page's `text_hash` is unchanged though bytes changed (timestamps,
  nonces) → no model re-extraction; a rule, being free, still runs.
- Expected result: an unchanged site costs one request per revisited page and zero model calls.
  A changed page costs one request, one parse, and one extraction.
- Business rules: full crawls are monthly; listings follow their own interval (news daily,
  projects weekly); model re-extraction is triggered by `text_hash`, never by time alone.

## UC-003: Compare two runs

- Goal: show a reviewer what a first run and an unchanged repeat cost.
- Actors: Operator.
- Preconditions: two runs exist.
- Main steps: `gov-mine run report <a> <b>` prints, per run, elapsed time, requests by outcome,
  files processed and failed, snapshots written, documents new and changed, records created and
  amended, paid calls by purpose, and cost by provider.
- Expected result: a markdown table suitable for the README.
- Business rules: every number is a query over `fetches`, `webpage_snapshots`,
  `classifications`, `extractions` and `ai_calls`; nothing is counted by the crawler itself.
  Model costs are actual, from the ledger. The report also gives an estimated monthly hosting
  cost, labelled as an estimate (section 13).

## UC-004: Demonstrate the three variants

- Goal: show an unchanged run, a changed source and a failed file without waiting for the site
  to change.
- Actors: Operator.
- Main steps: run twice (unchanged). Then `gov-mine dev replay` serves saved local copies with
  one project page edited (phase changed) and one PDF replaced by a corrupt file, and a run is
  pointed at it. The report and `gov-mine records history <id>` show the amended record and the
  failed snapshot.
- Business rules: replayed runs are marked in `crawl_runs.settings` so they are never confused
  with live runs.

## UC-005: Export for another service

- Goal: hand the records to a downstream system.
- Actors: Operator; downstream service.
- Main steps: `gov-mine export --since 2021-10-26 --out out/` writes one JSON Lines file per
  record type, one for citations, one for documents, and a `manifest.json` with the run id,
  extractor versions and counts.
- Business rules: every record carries its citations' webpage URL, page and excerpt; a document
  dated before `--since` is left out, an undated one is kept; the export is reproducible from
  the database alone.

## UC-006: Add a rule extractor for a page family

- Goal: make extraction for a known template free and deterministic.
- Actors: Developer with a coding agent.
- Preconditions: a family of document pages that share a template and a URL pattern, e.g.
  CreateTO project pages (`/projects/*`).
- Main steps: write the extractor config (for createto.ca, JSON paths into `__NEXT_DATA__`; for
  other sites, CSS selectors); run `gov-mine extract --dry-run --source <id>` against stored
  snapshots; compare with the model's output; store the config, with its URL pattern, on the
  source. From then on every document whose URL matches the pattern uses the rule, whether or
  not it was found under that source.
- Alternative flows: the rule's output fails Pydantic validation on a page → the model runs
  with `fallback_reason = validation_failed`; a rule that fails on many pages is the alarm that
  the template changed.
- Business rules: a rule extractor is a named version (`rule:createto_project@1`). A new
  version, like a changed prompt, is applied to stored pages only when rerun by hand (`gov-mine
  extract --rerun`).

## UC-007: Add an institution and crawl it from the dashboard

- Goal: point gov-mine at any public institution's website without touching code.
- Actors: Operator (in the browser).
- Preconditions: the service, a worker and the scheduler are running.
- Main steps:
  1. Operator opens Institutions, clicks Add, enters name, type and website URL, and saves. The
     host is created as a `crawl` domain.
  2. Operator clicks Start full run. The run appears in Runs as `queued`, then `running`, with
     live counts from the fetch log (fetched, not modified, skipped, blocked, failed),
     snapshots written, documents found, records extracted, and cost so far.
  3. Operator opens the run: a table of fetches filterable by outcome; the sources found with
     their intervals; the documents by type; the records by type with their citations; the
     report.
  4. Operator opens a record: its typed fields, each with its citation (link, page, excerpt,
     verified), and its history of record snapshots.
- Alternative flows: the website URL does not respond → the run fails with the error shown on
  the run page. A host policy needs changing (a partner host should be files only) → Domains
  page, edit policy, re-run.
- Expected result: the same outcome as UC-001, driven and inspected from the browser.
- Business rules: everything the dashboard shows is read from the tables; it never computes its
  own counts.

## UC-008: The scheduler keeps institutions current

- Goal: re-runs happen without anyone remembering to start them.
- Actors: the scheduler (a Procrastinate periodic task in the worker).
- Main steps: every minute, for each institution with a source whose `next_crawl_at` has passed
  and no run in progress, create an incremental run; for each institution whose last full run
  is older than its full interval (default 30 days), create a full run. Runs created this way
  carry `trigger: scheduled` in `settings`.
- Alternative flows: a run is already running for the institution → skip until it finishes. The
  per-run cost ceiling is reached → the run finishes with a warning shown in the dashboard and
  the sources' `next_crawl_at` still advance.
- Business rules: at most one run per institution at a time; the scheduler never creates a run
  for an institution marked paused in the dashboard.

## UC-009: Review low-confidence results

- Goal: a person checks the classifications and extractions the system is least sure of.
- Actors: Reviewer (in the browser).
- Preconditions: at least one run has finished.
- Main steps:
  1. Reviewer opens Review: a list of items below the confidence thresholds with no review
     decision yet, each with its page, the classifier's choice or the extracted fields, and the
     confidence.
  2. Reviewer opens an item: for a classification, the page and the choice; for an extraction,
     each field with its citation and verified flag.
  3. Reviewer clicks Approve or Reject, optionally with a note.
- Alternative flows: the reviewer changes their mind → a new review decision replaces the old
  one. The page changes later → its new extraction is a new item (a page is classified
  only once).
- Expected result: rejected classifications stop their source being crawled and their document
  being extracted and exported; rejected extractions drop out of records and export.
- Business rules: review decisions are append-only; the latest counts; the queue is a query.

## UC-010: RFPs and awards from a procurement platform (MERX)

- Goal: get an institution's tenders, and the vendors that won them, when it publishes them on
  a shared platform rather than its own site.
- Actors: Operator; MERX.
- Preconditions: `www.merx.com` is a `platform` domain; the MERX rule (`rule:merx@1`) is in
  code.
- Main steps:
  1. A full crawl of createto.ca reaches the Procurement page, which links to the MERX search
     for "createto". The link is on a `platform` host and matches the MERX rule's search
     pattern, so it is followed.
  2. The search becomes a `listing:rfp` source of the run's institution, typed by the rule, not
     the classifier. The rule expands it into its open, closed and awarded tabs with the same
     keywords, and their pages are fetched 5 s apart.
  3. Each tender page becomes an `rfp` document; the rule reads its labelled fields into an
     `rfp` record.
  4. An awarded tender's page carries its award panel URL; the panel becomes a document of the
     tender (`parent_document_id`), and the rule reads it into a `contract` record with
     `origin = award`.
- Alternative flows: a tender whose Issuing Organization does not contain the institution's
  name (a keyword match on someone else's tender) is kept as a snapshot and yields no document.
  Login-only panels (documents, plan holders) never match a pattern and are never fetched. A
  changed MERX template fails validation, which shows as `fallback_reason = validation_failed`.
- Expected result: for CreateTO, about 120 tenders and 84 awards from about 215 requests
  (about 18 minutes at 5 s), with no model calls.
- Business rules: the MERX source is revisited weekly; an awarded tender is final and is not
  revisited; documents dated before the cutoff are kept but not exported.
