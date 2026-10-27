---
name: spec-to-tickets
description: Breaks a spec markdown file into vertical-slice tickets, one markdown file per ticket in backlog/, each sized for a single /implement-ticket session.
argument-hint: "[path to spec .md]"
disable-model-invocation: true
---

# Spec to tickets

Spec: $ARGUMENTS

Turn the spec into tickets that can each be implemented, tested, and reviewed in their own sessions. Those sessions see only the ticket and the spec, so a ticket's acceptance criteria are its definition of done and the source of its tests.

## 1. Read

- Read the spec in full, and every file in `backlog/` so numbering continues and nothing is ticketed twice.
- Skim the code the spec touches, enough to know what already exists and how a change would cut through the layers. Tickets describe behavior, not files, so paths stay out of them.

## 2. Resolve gaps first

List every place the spec is silent, vague, or contradicts itself or the code where an implementer would have to guess. Ask the user, and wait for answers before drafting. A ticket requirement the spec doesn't support is a bug you'd be planting; record each answer in the affected ticket's Notes.

## 3. Draft vertical slices

- Each ticket is a thin end-to-end path (database, API, UI as needed) that delivers one behavior someone can observe, not one layer of many features.
- Ticket 1 is the thinnest working path through the whole feature; later tickets widen it.
- If the current code would force the feature in as a bolted-on special case, add a refactor ticket first that reshapes it with behavior unchanged, so the feature then lands as a natural extension. Make the change easy, then make the easy change.
- Size each to one focused session: a handful of acceptance criteria. Split a ticket that needs "and" to describe what it delivers.
- A change too wide to stay green in one slice (a rename across the codebase, a shared type change) goes expand → migrate in batches → contract, one ticket each. The contract ticket deletes the old path; never leave two ways to do one task.
- Order by dependency. "Depends on" lists only tickets that must land first.

## 4. Check with the user

Show a numbered list: title, depends on, and what it delivers in one line. Below it, a coverage table mapping every requirement in the spec to exactly one ticket. Anything unmapped needs a ticket; anything in a ticket but not in the spec comes out. Revise until the user approves.

## 5. Write the files

One file per ticket at `backlog/NNN-slug.md` (three-digit number, continuing from the highest in `backlog/`), in this form:

```markdown
# 004: Invite a member by email

Spec: specs/workspaces.md
Depends on: 002, 003

## What to build

A workspace owner invites someone by email. The invite appears as pending in the member list until it's accepted.

## Acceptance criteria

- [ ] An owner who submits a valid email sees the invite listed as pending.
- [ ] Inviting an address that is already a member returns 409 and creates no invite.
- [ ] A non-owner who tries to invite gets 403.

## Out of scope

- Accepting the invite (005).

## Notes

- Invites expire after 7 days (user decision, not in the spec).
```

- **What to build**: one or two sentences of user-visible behavior.
- **Acceptance criteria**: each one observable from outside (a response, the UI, stored data), with concrete values, and checkable by a single test. Include the error and edge behavior the spec defines.
- **Out of scope**: neighboring work an implementer might drift into, with the ticket that owns it. Omit when there is none.
- **Notes**: decisions and constraints the implementer needs that aren't in the criteria. Omit when empty.

Finish with the list of files written and the coverage table.
