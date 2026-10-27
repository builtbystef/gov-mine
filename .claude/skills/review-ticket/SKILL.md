---
name: review-ticket
description: Reviews a ticket's implementation and tests for code quality (structure, naming, complexity, reuse, error handling, test quality, scope) and reports ranked findings without editing. Run in a fresh session after /test-ticket.
argument-hint: "[backlog/NNN-*.md, issue number, or issue URL]"
disable-model-invocation: true
---

# Review a ticket

Ticket: $ARGUMENTS

You didn't write this code. Judge whether the next engineer can read it, change it, and trust it. Earlier sessions owned correctness and coverage; flag a bug if you see one, but quality is the focus. Report only: the user picks what to act on.

## 1. Gather

- Load the ticket: a path (usually `backlog/NNN-*.md`) → read the file; an issue number or URL → `gh issue view <ref> --comments`. Read the handoff notes with `git log main..HEAD` and the change with `git diff main...HEAD`.
- Run `vp run check` and `vp run test`. Any failure is the first finding. The linters already enforce formatting, complexity, argument counts, and magic numbers, so spend your attention on what they can't see.
- Read past the diff: the callers of changed code and the modules beside it. Search for similar names and logic; duplication and missed reuse only show up there.

## 2. Review the code

- **Simpler shape**: would the code look like this if the requirement had been known from the start? Look for a reframing that makes branches, flags, or helpers disappear, not just a tidier version of the same idea.
- **Bolted-on branches**: special cases or boolean modes added to an unrelated flow, the same condition checked in several places (a missing model), or a file pushed past ~500 lines with a second concern.
- **Depth**: wrappers that only forward arguments, interfaces with one implementation and no second in sight, casts, `Any`/`any`, and needless optionality hiding the real contract.
- **Responsibility**: each new function and module does one job you can name without "and", and sits in the layer where similar logic lives.
- **Names**: say what things are and do, in the project's own terms, consistent with nearby code.
- **Flow**: early returns, shallow nesting, complex conditions named.
- **Reuse**: nothing re-implements an existing helper, type, or pattern, and nothing is copy-pasted within the change. Code that is merged should change for the same reason; a forced abstraction is worse than duplication.
- **Real callers only**: no options, aliases, overloads, branches, or config that nothing uses. Agents add these "just in case".
- **Errors surface**: flag broad catches, swallowed errors, fallback defaults that hide missing data, `?.` or `or` defaults on values that must exist, and errors re-raised without context.
- **Hollow work**: stubs, hard-coded sample data, `TODO` returns, output with the right shape but not the right content.
- **Boundaries**: external input validated once where it enters; types that make invalid states unrepresentable.
- **Scope**: changes the ticket didn't ask for (refactors, config, dependencies, deletions), plus leftover debug code, scratch files, and commented-out code.
- **Comments and docstrings**: read every one the diff adds or leaves stale. Each must say what the code can't: why, a constraint from outside the code, an invisible invariant. Flag ones that restate the code or the signature, narrate the change or the ticket ("now", "added", "fixed", "used by X"), address a reviewer, or run to paragraphs where a line would do. A comment explaining surprising code of our own is a symptom: the fix is the rename, extraction, or type that makes it obvious, then delete the comment. A `do not remove` or `IMPORTANT` warning is a rule waiting for a test or type to enforce it. Comments the change made wrong are misleading code, since the next agent will believe them.

## 3. Review the tests

- Expected values come from the ticket, not from running or copying the code under test.
- Tests go through public seams and assert outcomes, not internal calls.
- Mocks sit only at real external boundaries. Flag mocks of the project's own modules or of the database.
- One behavior per test, named for it; no sleeps or order dependence.
- Missing tests matter for ticket criteria and realistic edge cases, not for cases the types rule out.

## 4. Calibrate

- Re-read the code behind each finding before keeping it. Drop any you can't tie to a line, and any that rest on a guess you haven't checked.
- Trace the call site before flagging a risky input: "what if this is null" only counts if a caller can pass null.
- Drop "I'd have done it differently" without a concrete cost, abstractions suggested for code that varies in only one way, and patterns consistent with the rest of the codebase.
- A reviewer asked for problems always finds some. Keep what will cause a bug or cost someone real time; drop matters of taste. Zero findings is a valid result.
- When a finding is a rule that a lint, type, or test could enforce, say so: the rule fixes every future instance, not just this one.
- Severity: **Must fix** (a bug, misleading code including wrong or stale comments, hidden errors, broken layering), **Should fix** (will slow down the next change, including redundant comments), **Consider** (optional; at most three).
- Group redundant comments into one finding that lists their lines, so they don't crowd out the rest.

## 5. Report

Findings ranked by severity, each as: `file:line` — what's wrong — the concrete consequence — the smallest fix. End with a one-line verdict: ready to merge, or ready after the must-fix items.
