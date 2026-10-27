# 3. Solution

- Proposed solution: a Python service with a CLI, an API and a web dashboard, backed by
  PostgreSQL and S3-compatible object storage, organised as three stages: **research**
  (institutions and their websites; a stub, one row by hand), **extraction** (crawl, ingest,
  classify, extract, cite, schedule), and **signals** (not built). Work is queued in
  PostgreSQL. Every paid call is a ledger row.
- Main capabilities:
  1. Crawl a site from its homepage with per-host robots, pacing and scope; download files on
     other hosts; log every attempt including skipped and blocked links.
  2. Keep a copy of each page and file as raw bytes plus one markdown representation per page.
  3. Classify each page once, when first fetched, as nothing, a listing of type X (a source
     with a schedule), or a document of type X. Files a project lists as its materials are
     that project's documents without asking the classifier.
  4. Extract typed records from documents, rule extractor first, model second, each field with
     a citation that is verified against the stored text.
  5. Re-run on a schedule with conditional requests, writing a new snapshot only on change and
     a new record state only when a field changed.
  6. Report a run: time, requests, files, records, paid calls and cost, as queries.
  7. Export records and citations as JSON Lines for another service.
  8. A built-in scheduler that creates incremental runs when sources are due and full runs on
     the institution's interval.
  9. A web dashboard to add any institution by name, type and website, start and watch a run,
     browse pages, documents, records and citations, and read the run report.
  10. A review queue: classifications and extractions below a confidence threshold, approved or
      rejected in the dashboard.
  11. Follow a procurement platform an institution's own pages link to (MERX first) and read
      its tenders and awards with one shared rule, so RFPs and winning vendors come in without
      a model.
- Outside the scope: finding institutions and their websites (research); signal templates and
  signals; shared aggregators beyond a procurement platform the institution itself links to
  (no USAspending, no searching state RFP portals on our own); vendor and product resolution;
  video transcription (the ledger purpose exists; no worker); correcting a value by hand in
  review (a reviewer approves or rejects); multi-tenant or customer data of any kind;
  authentication (the dashboard runs locally); noticing a page that drops off a listing but
  still loads (only a 404 counts as a removal); removing a record that a page stops mentioning
  (it keeps its last state).
- Known constraints:
  - createto.ca is a Next.js site on Storyblok, server-rendered, so plain HTTP fetching works
    and no browser is needed. Each page carries a `__NEXT_DATA__` JSON block with the page's
    structured content (a project's phase, ward, address, site area, timeline, resources,
    published and updated timestamps). Some linked files appear only in that JSON, not as links
    in the HTML (on the Parkdale Hub page, 8 of the 14 PDFs in the page body), so the crawler
    picks up every URL in the raw HTML, not only `<a href>` links. This works on any site, not
    just Next.js. Pages send an `ETag`. The sitemap lists 232 URLs: 137 news, 75 projects, 5
    initiatives, 5 about, 3 "our work", plus policy pages. Every sitemap `lastmod` is the
    site's last build time, so it says nothing about which pages changed. Files are hosted on
    `a-us.storyblok.com`, with some on `toronto.ca` and partners' sites.
  - The extraction window is the past five years, rolling: a run's cutoff is its start date
    minus five years (2021-10-27 for a run on 2026-10-27), recorded in the run's settings.
    Everything is crawled and kept regardless. A document's date (`documents.document_date`)
    follows one rule for pages and files alike: the latest date it states about itself, that is
    the later of its published and last-updated dates. For a file these come from its own
    metadata (PDF or office created and modified dates); for an HTML page, from its metadata
    (meta tags, JSON-LD, or embedded page data such as createto.ca's Storyblok `published_at`
    and `updated_at`), else from a date the extractor reads in the text. So a project page
    first published in 2019 and updated in 2024 is in the window. A document with no date is
    treated as current. Documents dated before the cutoff are not extracted; the export leaves
    them out.
  - Budget: model cost must be reported and estimated. Both models go through OpenRouter with
    one key: extraction uses `openai/gpt-6-luna` at USD 0.10 per million input tokens and 0.50
    per million output tokens (1.05M context, structured outputs, `reasoning_effort: medium` to
    start); classification uses `typesafe/jev-1.14` at USD 0.042 per million input tokens with
    output free, through OpenRouter's Decisions API (`POST /api/alpha/decisions`), not chat
    completions; it returns the chosen option, a probability per option and a confidence.
    (`typesafe/jev-router` is a different product that routes requests to other models.)
    Its request and response shapes are in section 8, as documented on 2026-10-27; whoever
    builds the adapter checks them against OpenRouter's and TypeSafe's documentation then.
    Scanned PDF pages are read by `openai/gpt-6-luna` too (OCR), at the same price.
  - Politeness: one request at a time per host, a default delay of 1 s or the host's robots.txt
    `Crawl-delay` when longer, robots.txt honoured, a descriptive user agent.
  - CreateTO posts its tenders on MERX (merx.com), not on its own site. Its Procurement page
    links to a MERX keyword search (`/public/solicitations/open?keywords=createto`). The
    search's open, closed and awarded tabs are public, server-rendered HTML with 25 results per
    page (`pageNumber=N`). On 2026-10-27: 1 open, 120 closed (back to 2016, under the name
    Build Toronto) and 84 awarded; the Bid Results tab is empty for CreateTO. The pagination
    repeats rows, so walking every page of each tab reaches 108 distinct tenders (1 open, 88
    closed, 74 awarded, overlapping) and 9 closed rows that link to a login-gated notice; the
    rest are not reachable this way, which phase 1 accepts (decision 34). A tender page shows
    labelled fields: reference and solicitation number, issuing organization ("CreateTO (Build
    Toronto, TPLC)"), type, title, description, location, publication and closing dates. An
    awarded tender's award (supplier, supplier address, value or "Undisclosed", award date) is
    public but loaded separately from `/public/solicitations/<id>/abstract/award`, which
    returns the panel's HTML inside a jQuery call, and only to a request that sends
    `X-Requested-With: XMLHttpRequest` (without it MERX returns its welcome page). Tender
    documents and the plan holders list need an account and are never fetched. MERX's
    robots.txt allows these pages for general crawlers, asks for `Crawl-delay: 5`, and blocks
    named AI crawlers (GPTBot, ClaudeBot and others). Every page carries a copyright notice.
  - Simplicity beats completeness; anything one query can answer is not stored.
- Transition from the current approach: none to transition from. The repository starts from
  Alloy, the author's web-app template (FastAPI, SQLAlchemy, Alembic, Procrastinate, the
  object-storage port, the Next.js app shell, the generated API client, CI and image builds,
  agent notes and skills). Its auth, workspaces, CRM, assistant, mail, rate-limit and evals
  modules are removed; auth and workspaces can come back from Alloy if the project continues
  past phase 1. Alloy's `ModelCall` table becomes `ai_calls`. The few Public Atlas pieces
  Alloy lacks are copied by hand: the quote check and checked-string enums. The CLI is written
  in Typer, following Public Atlas's pattern (each command builds resources as the API does and
  calls a service) rather than copying its argparse file (decision 25). No data is migrated.
  If the new system fails early, the snapshots (bytes and text in object storage) are still
  useful on their own.
