# 14. Decisions and Open Questions

- Decisions, reasons, and trade-offs:
  1. Sources are discovered by the crawl, not by a research stage. The crawl is exhaustive
     from the homepage; a source is just a listing page the crawl noticed. Trade: the first
     crawl reads everything; later runs are cheap.
  2. One type vocabulary for sources and documents (section 5.2), as an enum in code rather
     than a table. Trade: a new type is a code change, not a row.
  3. Snapshots are keyed by content. Unchanged runs cost requests only.
  4. One markdown representation per page serves hashing, classification, extraction and the
     quote check. Trade: markdown loses some layout; PDFs with complex tables may need Docling
     later.
  5. Rule extractors first, model as fallback; rules are written by a developer with a coding
     agent, not by the model at run time. For createto.ca the rule reads `__NEXT_DATA__`.
  6. Every field cites an excerpt. Model excerpts are checked by the quote check; rule excerpts
     are the raw value code read from the snapshot, so they need no check. Trade: fields the
     page states only in an image or a map (coordinates) cannot be cited and are stored
     unverified.
  7. Records are an identity row plus JSONB snapshots; record types are Pydantic models in
     code, not tables. One write per change and no migration per type. Trade: the database does
     not enforce field types (Pydantic does, before every write), and queries read
     `data->>'field'`; a view per type gives columns if needed.
  8. A general AI cost ledger (`ai_calls`) separate from extractions. One extraction may be
     many calls; OCR and transcription have no extraction.
  9. Nothing derivable is stored. Trade: the report is queries, which must be fast enough;
     indexes on `fetches(crawl_run_id, outcome)` and `ai_calls(crawl_run_id, purpose)`.
  10. No browser. createto.ca is server-rendered; a Playwright adapter stays a port.
  11. Jev 1.14 classifies every page once, when first fetched, behind a port, reached through
      OpenRouter's Decisions API. A page does not change what it is when its text changes, so a
      changed page is re-extracted, not re-classified. No model fallback and no rule-based
      classification: rules do not scale for classification, because every site names its
      pages differently (`about/`, `about-us/`, `about-the-org/`), and classifying is cheap.
      Extraction is the opposite: much more expensive per page, and a page family shares one
      template, so a rule written once with a coding agent pays for itself (decision 5). Either
      can be optimised later if the costs say so.
  12. `openai/gpt-6-luna` with `reasoning_effort: medium` for extraction, over OpenRouter,
      raised to high only if comparing outputs on saved pages shows better fields. Cheap
      enough (USD 0.10 in, 0.50 out per million tokens) that the whole CreateTO site extracts
      for well under a dollar, with a context window that takes any PDF whole.
  13. A full dashboard in phase 1, able to add and crawl any institution. A crawl should be
      something to watch, not read about. Alloy's app shell is reused, which keeps it cheap to
      build.
  14. A built-in scheduler in the worker rather than cron, so "consider re-running" is
      demonstrated running, with sources' intervals visible in the dashboard. It is a
      Procrastinate periodic task, so it never runs twice per tick.
  15. One Procrastinate queue with several job types, not one queue per stage. Per-host
      politeness is a Procrastinate job lock, not a hand-rolled advisory lock. Trade: paid jobs
      cannot be throttled separately from fetching; the cost ceiling covers that.
  16. Alloy's stalled-job sweep is kept: a periodic task requeues every job whose worker's
      heartbeat has stopped. It is already built, and every job is idempotent (section 8), so
      a second run is safe. Trade: a paid job killed after its model call but before its
      commit pays for that call again; the cost ceiling bounds it.
  17. Review is a queue (a query) plus a `review_decisions` table of approve or reject
      decisions. Confidence for classifications is Jev's probability; for extractions it is the
      share of verified citations, not a number the model reports about itself. Trade: a
      reviewer cannot correct a value, only reject it.
  18. A document's date is the latest date it states about itself (the later of published and
      last updated), from a file's or a page's metadata, else from the text; an undated
      document counts as current. One rule for pages and files, and a project still being
      updated stays in the window. Trade: metadata can be wrong (a re-saved old file, or a
      site-wide re-publish, looks new), which errs towards keeping too much rather than too
      little.
  19. Records a page stops mentioning are not removed in phase 1; they keep their last state.
  20. A changed extractor is rerun by hand (`gov-mine extract --rerun`), never automatically.
      Trade: old pages keep results from the old version until someone reruns it.
  21. A record is identified by its document, its type and a key field for documents that hold
      several. Trade: the same project described on two pages is two records; matching them is
      a later job.
  22. A file listed in a project's materials is a `project_material` document of that project,
      assigned by the project's extraction, not by the classifier. Trade: a file parsed before
      its project page was extracted has already been classified once; the project assignment
      overrides that type.
  23. `text_hash` covers the page's links as well as its text, and rule extractors run on every
      new snapshot. Some sites put file links only in scripts or embedded JSON (8 of the 14
      PDFs on the Parkdale Hub page), which the markdown drops; adding the sorted link list to
      the hash catches a file added or removed there, on any site. Data that lives only in the
      JSON (a project's phase or ward) is caught by the rule, which is free, and a record
      snapshot is still written only when the data changed. Only the model waits for
      `text_hash`. Trade: a site that rotates link parameters on every build would look
      changed each time; the link list is normalised like every URL (section 10).
  24. A procurement platform is a host policy (`platform`) plus one rule per platform in code,
      not a research stage. CreateTO's tenders are only on MERX, linked from its own
      Procurement page, so following that one link is what brings in RFPs and winning vendors.
      The rule types the pages itself (no classifier), reads labelled fields (no model), and
      works for every institution that posts on MERX. Trade: the award panel is an internal
      AJAX URL that MERX could change without notice; a failing rule shows up as
      `validation_failed`.
  25. The repository starts from Alloy, not Public Atlas. The two share one skeleton, but Alloy
      is the more recent and cleaner, and carries the agent notes and skills the coding agent
      works from; what Public Atlas adds is mostly the agent, review, evals and imports modules
      this project drops. The few pieces worth having (the quote check, checked-string enums)
      are copied by hand, and the CLI follows Public Atlas's pattern in Typer. Trade: Alloy's
      auth, workspaces, CRM and assistant must be removed first; auth
      and workspaces come back from Alloy if the project continues.
  26. The demo is hosted on Railway with no authentication, at an unlisted URL shared
      privately, and taken down after the demo. Railway runs the whole app (services,
      PostgreSQL, bucket) with the least setup, and the demo is short-lived. Trade: anyone
      with the link can start runs and spend model budget; the per-run cost ceiling (USD 5)
      and the OpenRouter key's limit bound it. Auth comes back from Alloy if the app stays up.
- Assumptions: none at the time of writing.
- Open questions and owners: none at the time of writing.
- Possible later additions (not in phase 1; owner: the author):
  - Check the value as well as the excerpt. The quote check confirms an excerpt is on the
    page, not that it supports the field: `start_date = 2024-03-01` with the excerpt
    "Construction is expected to begin in 2025" passes today. A later check would require the
    normalised value (dates in common formats, numbers without separators, case folded) to
    appear inside its excerpt, and mark free-text fields such as `description` as "excerpt
    found" rather than verified.
- Risks and dependencies:
  - The hosted demo's URL is shared further. Mitigation: the cost ceiling and the
    key's provisioned limit; the Railway project is deleted after the demo (decision 26).
  - The site or its host (Vercel) blocks the crawler's IP. Mitigation: one request at a time
    per host with a 1 s delay, robots.txt honoured, a descriptive user agent, conditional
    requests on re-runs; saved local copies let the variants run without the site.
- Additional client or project context: none at the time of writing.
