# 051: Show settings

Spec: docs/specification/09-external-interfaces.md (Settings)
Depends on: 042

## What to build

A Settings page shows the versions, models, prices and limits gov-mine is running with.

## Acceptance criteria

- [ ] `GET /settings` returns extractor and parser versions, the extraction and classification models, the price list version, the default cost ceiling, and the review thresholds.
- [ ] The Settings page shows them, read-only.
- [ ] No secret, such as the OpenRouter key, appears in the response.
