# 10. Cross-Cutting Concerns

- Authentication and authorization: none in phase 1; Alloy's auth and workspaces are removed
  (section 3). Locally the API and dashboard bind to localhost; the hosted demo is an unlisted
  URL with no login (section 13). Provider keys are the only secrets.
- Logging and audit records: structured logs (Alloy's JSON logging with context variables;
  Logfire traces off unless `GOV_MINE_LOGFIRE_TOKEN` is set) with run id, job id and webpage id
  on every line. The audit trail is the data itself: `fetches`, `classifications`,
  `extractions`, `ai_calls`, `record_snapshots` and `review_decisions` are append-only.
- Error handling: exceptions at ports are typed (`FetchError`, `ParseError`, `ProviderError`,
  `ValidationError`); job functions catch them and write the outcome row, then re-raise only
  when a retry is wanted. No silent `except`.
- Configuration and secrets: `GOV_MINE_*` environment variables, documented in `.env.example`;
  pydantic-settings; keys never logged.
- Transactions and consistency: a job's writes and its completion commit together; a snapshot
  is written to object storage before its row is inserted (an orphan object is harmless, an
  orphan row is not); upserts use `ON CONFLICT` on the unique keys in section 5.
- Other shared concerns: time is UTC everywhere; URL normalisation is one function (scheme,
  host case, default port, fragment, trailing slash, tracking parameters); the markdown
  normaliser used by the quote check is the same one used to compute `text_hash`.
