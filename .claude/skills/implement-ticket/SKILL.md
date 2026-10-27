---
name: implement-ticket
description: Implements one ticket, exactly as scoped, and verifies it by running the code. Tests come later in a separate /test-ticket session, and review in /review-ticket.
argument-hint: "[backlog/NNN-*.md, issue number, or issue URL]"
disable-model-invocation: true
---

# Implement a ticket

Ticket: $ARGUMENTS

Make the ticket's behavior work, correctly and completely, and nothing beyond it. Separate sessions write the tests and review the code; they only know what the ticket and your commit message tell them.

## 1. Understand the ticket

- Load it: a path (usually `backlog/NNN-*.md`) → read the file; an issue number or URL → `gh issue view <ref> --comments`. Read the parent spec if it links one.
- Restate its acceptance criteria as a numbered list. That list is your definition of done.
- If the ticket is ambiguous, contradicts the code, or leaves a real decision open, ask before building. Check your plan against what the ticket asks, not against requirements you inferred: an invented requirement is a bug, however sensible it looks.

## 2. Read before writing

- Find the code the change touches, its callers, and existing helpers, types, and patterns that already do part of the job. Extend those; a second version of something that exists is a defect.
- Check library APIs against the installed version (`node_modules/<pkg>`, `.venv/lib/python3.14/site-packages/<pkg>`), not memory. Dependencies here are often newer than your training data.
- On `main`, branch first: `git switch -c ticket-<number>-<slug>`.

## 3. Build

- Make the smallest change that fully meets every criterion, shaped as if the requirement had been there from the start rather than a special case bolted onto an unrelated flow. Build for the callers that exist: no options, aliases, overloads, or branches for inputs nothing sends.
- One way to do each task. When the ticket replaces an API or pattern, migrate every caller and delete the old one in the same change: no shims and no parallel old and new paths. After a rename, search strings, docs, and config for the old name too.
- Touch only what the ticket needs. Problems you notice elsewhere go in the report, not the diff: no drive-by refactors, renames, config or dependency changes, or deletions.
- Let unexpected states fail loudly. Handle an error only where the ticket defines what should happen; otherwise no broad `except`/`catch`, no fallback default that hides missing data, no `?.` or `or` covering a value that must exist.
- Deliver real behavior. A stub, hard-coded sample data, or output with the right shape but not the right content is unfinished work; if you can't finish a criterion, stop and say so.
- Match the surrounding code's naming and structure.
- Default to no comments. Agents over-comment, and every comment is one more thing the next reader, often another agent, takes as true and must keep true. If code needs a comment to say what it does, rename or extract until it doesn't. Comment only what the code can't say: why it is this way, a constraint from outside the code (a library quirk, a protocol, a deadline), an invariant that isn't visible. Never narrate the code, describe the change or the ticket ("now", "added", "fixed", "used by X"), or address a reviewer; that belongs in the commit message. Docstrings only where a public function's contract isn't obvious from its name and types, and then one line: no blocks that restate the parameters.
- A model change needs an Alembic migration. An API shape change needs `vp run generate`.

## 4. Verify

- For a refactor ticket, pin the behavior first: tests that cover what the code does today must exist and pass before you move anything, and pass unmodified after.
- Exercise each criterion for real: call the endpoint, run the function from a scratch script, load the page. A passing typecheck is not evidence the behavior works. Delete scratch code afterwards.
- Check off each criterion in the ticket as soon as you have verified it: `- [ ]` to `- [x]` in the backlog file, or in the issue body with `gh issue edit`. A criterion you couldn't verify stays unchecked. The ticket file's edits go in the ticket's commit.
- Read every comment and docstring your diff adds (`git diff`) and delete each one that fails the rule above. Writing them is a habit, so this pass is where they get caught.
- `vp run check` passes. Run the tests near your change while you work (`uv run pytest <path>`, `vp test <path>`), then the full `vp run test` once at the end. Integration tests need `vp run db:up`.
- New tests are /test-ticket's job. When an existing test fails, work out whether the code or the test is wrong. Change a test only when the ticket deliberately changes that behavior. Deleting, skipping, or loosening a test, or adding a lint or type ignore, to get green is never the fix.

## 5. Commit and report

Commit on the branch as `<ticket ref>: <what changed>`, with this report as the commit body (the later sessions read it with `git log`), and give the same report to the user:

- **Criteria**: each one, done or not, and how you verified it (the command and what it showed).
- **Not verified**: anything you believe works but didn't observe. "Should work" belongs here.
- **Decisions**: where the ticket was silent and you chose.
- **Changed tests**: which ones and why.
- **Out of scope**: problems noticed and left alone.
