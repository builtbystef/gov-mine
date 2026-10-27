# 018: Record paid calls in `ai_calls`

Spec: docs/specification/ (sections 3, 5.7, 8 `ledger.record`, 10)
Depends on: 002

## What to build

A refactor of Alloy's model-call recording into the spec's cost ledger. OpenRouter settings replace the OpenAI settings, and `ai_calls` replaces `model_calls`: one row per paid call, its cost computed from a versioned price list in code.

## Acceptance criteria

- [x] Settings read `GOV_MINE_OPENROUTER_API_KEY`, `GOV_MINE_EXTRACT_MODEL` (default `openai/gpt-6-luna`), `GOV_MINE_CLASSIFY_MODEL` (default `typesafe/jev-1.14`) and `GOV_MINE_EXTRACT_REASONING_EFFORT` (default `medium`); the old OpenAI settings are gone, and `.env.example` documents the new ones.
- [x] `ledger.record` for `openai/gpt-6-luna` with 1,000,000 input and 1,000,000 output tokens stores cost 0.60 USD; for `typesafe/jev-1.14` with 1,000,000 input tokens it stores 0.042. Each row carries the `price_list_version`.
- [x] `ledger.record` for a model not in the price list raises, and no row is written.
- [x] An `ai_calls` row stores the run, purpose (`classify`, `extract`, `ocr`, `transcribe`), provider, model, input and output tokens, and the optional classification or extraction id.
- [x] The `model_calls` table no longer exists, and nothing refers to `ModelCall`.
- [x] With no OpenRouter key set, nothing calls a model, and the key never appears in logs.

## Out of scope

- The first callers: classification (019), extraction (023), OCR (034).

## Notes

- Add the index on `ai_calls (crawl_run_id, purpose)`.
- The extraction and OCR model go through Pydantic AI over OpenRouter; Jev does not (019).
