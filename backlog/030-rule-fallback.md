# 030: Fall back to the model when a rule fails

Spec: docs/specification/ (sections 4 UC-006, 5.6, 14 decision 30)
Depends on: 029

## What to build

When a rule's output fails validation, typically because a template change broke its path for the identifying field, the model extracts the document instead and the extraction says why.

## Acceptance criteria

- [ ] A project page whose `__NEXT_DATA__` has no project name fails the rule's validation; the failed rule extraction keeps its error.
- [ ] The same document is then extracted by the model, with `fallback_reason = validation_failed`.
- [ ] A document with no matching rule is extracted by the model with `fallback_reason = no_rule`.

## Notes

- There is no `mostly_empty` check (user decision, decision 30).
