---
name: ship-ticket
description: Implements one ticket (or a few small ones) and tests its main path in a single session, then commits. The fast loop for demo work; /implement-ticket, /test-ticket and /review-ticket stay the thorough one.
argument-hint: "[backlog/NNN-*.md, several paths, issue number, or issue URL]"
---

# Ship a ticket

Tickets: $ARGUMENTS

Make each ticket's behavior work for real, cover its main path with tests, and commit. Speed matters more than polish here, but a demo that breaks is worse than a slower one: no stubs, no fake data.

## 1. Understand

- Load each ticket: a path (usually `backlog/NNN-*.md`) → read the file; an issue number or URL → `gh issue view <ref> --comments`. Skim the parent spec only where the ticket points to it.
- Restate the acceptance criteria as a numbered list. Ask only when a real decision is open; otherwise pick the simplest reading and note it under **Decisions**.

## 2. Build

- Find the code the change touches and the helpers, types, and patterns that already exist; extend them rather than writing a second version.
- Check library APIs against the installed version (`node_modules/<pkg>`, `.venv/lib/python3.14/site-packages/<pkg>`), not memory.
- Make the smallest change that meets every criterion, matching the surrounding code. No drive-by refactors, no options nothing uses, no fallbacks that hide missing data.
- Default to no comments; keep only ones that say why.
- A model change needs an Alembic migration. An API shape change needs `vp run generate`.

## 3. Test

- Write tests for the main path of each criterion, plus any error case the ticket names explicitly. Expected values come from the ticket, not from running the code.
- Follow the layout of neighboring tests: Python in `apps/server/tests/{unit,integration}`, TypeScript next to the source as `*.test.ts`. Use the real database (`vp run db:up`); mock only external network, the model, time, and randomness.
- Skip mutation checks and exhaustive edge cases. If something risky is left untested, say so under **Not tested**.
- Run the tests near the change while you work (`uv run pytest <path>`, `vp test <path>`).

## 4. Verify and commit

- Exercise the demo-visible behavior once for real (run the command, call the endpoint, load the page), and check off each criterion you saw work: `- [ ]` to `- [x]` in the backlog file.
- `vp run check` and `vp run test` pass. When an existing test fails, fix the code unless the ticket deliberately changes that behavior; never skip or loosen a test to get green.
- Commit on `main` as `<ticket ref>: <what changed>` (one commit per ticket when shipping several), with a short body:
  - **Criteria**: each one and how it was verified.
  - **Not tested**: what and why.
  - **Decisions**: where the ticket was silent.
  - **Out of scope**: problems noticed and left alone.
- Give the user the same report.
