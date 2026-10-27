# 8. Module Interfaces

## ingest.store(webpage_id, bytes, media_type) → snapshot_id | None

- Provider: ingest. Consumers: crawl.
- Purpose: persist a fetched body once per distinct content.
- Inputs: the webpage, the bytes, the media type from the response.
- Outputs: the new snapshot id, or `None` when the content hash already exists for that
  webpage.
- Errors: storage unavailable (raises; the fetch job retries).
- Rules and guarantees: idempotent on (webpage, content hash). Enqueues parsing itself.

## ingest.text(snapshot_id, page) → str

- Provider: ingest. Consumers: classify, extract, the quote check, the CLI.
- Purpose: the one text representation.
- Errors: `TextNotReady` when status is `parsing`; `NoText` when `none` or `failed`.
- Rules: markdown; stable for a given (snapshot, parser version).

## Parser port: parse(bytes, media_type) → list[str] pages, parser_name, stated_date | None

- Provider: ingest adapters (html, pdf, office, text). Consumers: ingest.
- Rules: pure; raises `ParseError` with a message that is stored as `text_error`. `stated_date`
  is the later of the published (or created) and modified dates in the content's metadata,
  when it has any.

## Classifier port: classify(url, title, text_head, links, choices) → (choice, confidence)

- Provider: `jev` adapter (`typesafe/jev-1.14` via OpenRouter's Decisions API), the only
  adapter. The model id is pinned, never the `~typesafe/jev-latest` alias: probabilities
  differ between versions, and the review threshold is tuned to one. Consumers: classify.
- Inputs: the page's URL and title, up to 100 link texts and hrefs (at most 6,000 bytes),
  the markdown from the top, cut at a paragraph boundary to fill the rest, and the choice set
  (`none`, and `listing:<type>` and `document:<type>` for every document type except
  `project_material`: 25 choices, each with a one-sentence description). The whole request
  stays under 32,000 bytes: above that TypeSafe runs a long-context mode it describes as
  slower and less accurate.
- Wire format: `POST /api/alpha/decisions` with `{"model": "typesafe/jev-1.14", "state":
  {"url", "title", "links", "text"}, "questions": {"page_type": {"type": "choice",
  "instructions": "...", "criteria": {"<choice>": "<description>", ...}}}}`. The answer is
  `answers.page_type` with `choice`, `probabilities` (per option) and `confidence` (how
  peaked the distribution is); `usage` has `input_tokens`, `output_tokens` and `cost`. The
  classification's `confidence` is `probabilities[choice]`; the whole answer is
  `raw_output`.
- Outputs: one choice and its probability in [0, 1] (Jev also returns a probability per option
  and a confidence; both are kept in the classification's `raw_output`).
- Errors: provider error (retry once); input too long (the adapter cuts the text to keep the
  request under 32,000 bytes, never fails).
- Rules: every call records an `ai_calls` row with purpose `classify` before returning.

## Extractor port: extract(document, text pages, record_type) → list[RecordDraft]

- Provider: `rule` adapter (config-driven), `model` adapter (structured output). Consumers:
  extract.
- Outputs: drafts validated by the record type's Pydantic model, each field with a draft
  citation (page, excerpt), and the page's publication date if it states one.
- Errors: `ValidationError` (the model adapter is tried next with `fallback_reason`); provider
  error.
- Rules: the adapter is named and versioned (`rule:createto_project@1`, `model:project@1`); the
  model name is part of the version string.

## ledger.record(run_id, purpose, provider, model, usage, classification_id=None, extraction_id=None) → ai_call_id

- Provider: ledger. Consumers: classify, extract, future workers.
- Rules: computes cost from the price list; unknown model raises before the call is made, so no
  call is ever unpriced.

## Events (jobs)

- One queue. Job types: `crawl.start(run_id)`, `crawl.fetch(run_id, webpage_id, depth)` (locked
  per domain), `crawl.finish(run_id)`, `ingest.parse(run_id, snapshot_id)`,
  `classify.page(run_id, snapshot_id)`, `extract.document(run_id, document_id,
  extractor=None)`, and the periodic `scheduler.tick()` and `jobs.retry_stalled()`.
- Every job except the two periodic ones carries `run_id`, so the rows it writes get their
  `crawl_run_id` and `crawl.finish` can tell when a run has no work left. `run_id` is null only
  for an extraction rerun by hand from the CLI.
- Guarantees: at-least-once; every job function is idempotent on its inputs, which the dedupe
  keys above make true.
