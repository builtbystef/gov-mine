# 029: Extract CreateTO project pages with a rule

Spec: docs/specification/ (sections 4 UC-006, 5.5, 5.6, 7 step 6, 14 decision 5)
Depends on: 027

## What to build

A rule extractor in code, `rule:createto_project@1`, reads a CreateTO project page's `__NEXT_DATA__` into a `project` record. `gov-mine sources set-rule` attaches it to a source, and from then on every document whose URL matches its pattern uses the rule, for free, on every new snapshot.

## Acceptance criteria

- [ ] `gov-mine sources set-rule <source id> rule:createto_project@1` copies the rule's URL pattern (`/projects/*`) and field paths into `sources.extractor_config`; an unknown rule name exits non-zero.
- [ ] A saved CreateTO project page extracts with `extractor = rule:createto_project@1`, gives the name, location, phase and other fields from `__NEXT_DATA__`, and makes no model call.
- [ ] Each rule citation's excerpt is the raw value read from the snapshot, with `verified = true`.
- [ ] A project page reached through the menu (no `source_id`) still uses the rule, because its URL matches the pattern.
- [ ] A new snapshot with an unchanged `text_hash` is still extracted by the rule, and changed data in `__NEXT_DATA__` produces a new record snapshot.

## Out of scope

- Falling back when the rule fails (030). Dry runs (031).

## Notes

- Rules are named versions kept in code; a new version is applied to stored pages only by a hand-started rerun (032).
- Patterns of one institution's sources must not overlap (section 5.6). Refusing a `set-rule` that would make them overlap is how this ticket enforces it.
