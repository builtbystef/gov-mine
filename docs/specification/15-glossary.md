# 15. Glossary

- Institution: a public body with a website. The subject of everything.
- Domain: a host, with its crawl policy, robots cache and delay.
- Platform: a shared site many institutions publish on, such as MERX for tenders. A
  `platform` domain is followed only where its platform rule's URL patterns match.
- Platform rule: a rule extractor in code, keyed by a platform's host, that says which of its
  URLs to follow, what each one is, and which fields to read. Written once per platform.
- Webpage: one URL ever seen. An address, not a claim.
- Fetch: one attempt at a URL, sent or refused, with an outcome.
- Webpage snapshot: a stored copy of a URL's content at a fetch: raw bytes and markdown per
  page. Written only when the bytes changed.
- Text hash: the hash of a snapshot's markdown with navigation and nonces stripped, plus the
  sorted list of links found anywhere in the raw content. What "changed" means for the model.
- Source: a page that lists documents of one type, revisited on an interval. Found by the
  crawl.
- Document: a page or file worth keeping, of one type, owned by one institution. Its versions
  are its webpage's snapshots.
- Document type: the enum shared by sources and documents (section 5.2).
- Project material: a file listed in a project's materials; a document of that project
  (`parent_document_id`), assigned without the classifier.
- Document date: the latest date a document states about itself (the later of published and
  last updated), from metadata or the text. Decides the five-year window; undated counts as
  current.
- Classifier: decides none, listing of type X, or document of type X for a snapshot.
- Extractor: turns a snapshot's text into record drafts. A rule extractor reads a known
  template; a model extractor reads prose.
- Classification: one run of the classifier over a webpage's first snapshot with text: its
  choice and confidence. A page is classified once.
- Extraction: one run of one extractor over one snapshot. The dedupe unit.
- Record: one thing a document describes (a project, a meeting), identified by type, document
  and key. Its current state is its latest record snapshot whose extraction was not rejected in
  review.
- Review queue: classifications and extractions below their confidence threshold with no review
  decision yet. A query.
- Review decision: a reviewer's approve or reject of one classification or extraction.
- Record type: a Pydantic model in code (`project`, `news_item`, ...) that defines a record's
  fields, gives the extractor its schema and validates its output.
- Record snapshot: one state a record has been in, written only on change.
- Citation: for one field of one record snapshot, the page and excerpt it came from. A model
  excerpt is verified by the quote check; a rule excerpt is verified by construction.
- Quote check: code that confirms an excerpt appears in the snapshot's text at that page.
- Ledger (`ai_calls`): one row per paid call, with purpose, provider, model, tokens and cost.
- Run: one crawl of one institution, full or incremental, with the settings it used.
- Fence: the ordered checks a URL passes before a request is sent.
- Replay: serving saved copies of pages locally to demonstrate the variants.
- Scheduler: the Procrastinate periodic task that creates runs when sources are due or a full
  run is overdue.
- Dashboard: the Next.js web interface over the API.
