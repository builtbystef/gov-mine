# 019: Classify each new page with Jev

Spec: docs/specification/ (sections 4 UC-001 step 4, 5.2, 5.6, 6, 7 steps 4–5, 8 classifier port, 9, 14 decisions 11 and 36)
Depends on: 015, 018

## What to build

Each webpage is classified once, on its first snapshot with text, by Jev through OpenRouter's Decisions API, as `none`, `listing:<type>` or `document:<type>`. The classification and its cost are stored, and the run page gains an AI calls tab.

## Acceptance criteria

- [ ] A newly parsed snapshot of a webpage with no classification enqueues `classify.page`, which writes one `classifications` row (`classifier = jev:classify@1`) and one `ai_calls` row with purpose `classify` linked to it.
- [ ] The request body sent to `POST /api/alpha/decisions` names the pinned model `typesafe/jev-1.14`, puts URL, title, links and text in `state`, and asks one `page_type` choice question with 25 criteria: `none`, and `listing:<type>` and `document:<type>` for every document type except `project_material`, each with a description.
- [ ] The request stays under 32,000 bytes for a page of any length: at most 100 links within 6,000 bytes, and the markdown from the top cut at a paragraph boundary to fill the rest.
- [ ] `choice` is Jev's choice, `confidence` is that choice's probability, and `raw_output` holds the whole answer, including every probability and Jev's own confidence.
- [ ] A later snapshot of an already-classified webpage is not classified again, and a retried job for the same snapshot writes no second row.
- [ ] A provider error is retried once; if it fails again, the classification row records the error.
- [ ] `GET /ai-calls?run=<id>` lists the run's paid calls, and the run page's AI calls tab shows them by purpose with cost.

## Out of scope

- Creating sources and documents from the choice (020). Review of low-confidence classifications (052).

## Notes

- The adapter is a thin httpx client, not Pydantic AI: the Decisions API isn't chat completions. Check the request and response shapes against OpenRouter's and TypeSafe's documentation when building (user decision).
- The 32,000-byte budget and one 25-way question are user decisions (decision 36).
- `DocumentType` comes in here, including `staff_directory` (decision 35).
