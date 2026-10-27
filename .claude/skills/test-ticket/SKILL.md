---
name: test-ticket
description: Writes tests for an implemented ticket, taking expected behavior from the ticket rather than the code, and proves each test can fail. Run in a fresh session after /implement-ticket.
argument-hint: "[backlog/NNN-*.md, issue number, or issue URL]"
disable-model-invocation: true
---

# Test a ticket

Ticket: $ARGUMENTS

Prove the implementation does what the ticket says, or find where it doesn't. The ticket is the source of truth, not the code: a test bent to match the code checks nothing, and a bug you find is a good result.

## 1. Write the test list from the ticket

- Load it: a path (usually `backlog/NNN-*.md`) → read the file; an issue number or URL → `gh issue view <ref> --comments`. Read the implementer's notes with `git log main..HEAD`.
- Before opening the implementation, list the behaviors to test, each with its expected result as the ticket defines it: every acceptance criterion, its boundaries (empty, limits, off-by-one), invalid input, and the error and permission paths the ticket implies.
- Leave out cases the ticket and the types rule out.

## 2. Find the seams

- Now read the diff (`git diff main...HEAD`) to find the public interfaces: the HTTP endpoint, the exported function, the component as a user sees it. Test there; internals can change without breaking a good test.
- Read two or three neighboring test files and follow their layout, fixtures, and naming. Python tests live in `apps/server/tests/{unit,integration}`; TypeScript tests sit next to the source as `*.test.ts`.

## 3. Write the tests

- One behavior per test, named for the behavior and its expected outcome. The name is the documentation: no docstrings that repeat it and no `# Arrange`/`# Act`/`# Assert` or step-by-step comments. A comment earns its place only to show how a hand-worked expected value was derived.
- Hard-code expected values from the ticket or work them out by hand. Computing them with the code under test, or a copy of its logic, makes a test that can't fail.
- Assert on outcomes the ticket cares about (response body, stored row, rendered text), not on which internal functions were called. Assert what the contract promises, no less and no more: the status or error type callers branch on, not exact error wording nobody reads.
- When the behavior is that something doesn't happen ("an empty cart never charges"), pair the test with one where it does, so the test shows it can see the effect.
- Use real collaborators. Mock only what can't run locally: external network APIs, the model, time, randomness. PostgreSQL and object storage run locally (`vp run db:up`); use them rather than mocking the project's own modules.
- No sleeps and no dependence on test order or the wall clock.

## 4. Prove the tests can fail

For each criterion, break the implementation on purpose (flip a condition, return early, drop a field), run the tests, and confirm one goes red. Then restore the file with `git checkout -- <file>`. A criterion that no break can turn red has no real test yet; fix the test.

The opposite check matters too: imagine restructuring the internals while every observable result stays the same. A test that would fail is pinned to the implementation; rewrite it against the interface.

## 5. Handle failures

- **The code is wrong** (it disagrees with the ticket): keep the test as written, leave the implementation alone, and report it as a bug.
- **The test is wrong**: fix it by re-reading the ticket, not the code.
- **The ticket doesn't say**: ask the user. Defaulting to whatever the code does turns the test into a copy of the code.

## 6. Finish

- `vp run check` passes, and `vp run test` passes apart from tests for reported bugs.
- With no bugs, commit as `<ticket ref>: tests for <what>`, with the report as the commit body. With bugs, leave the tests uncommitted so the user can decide who fixes the code.
- Report:
  - **Coverage**: each behavior → the test that covers it.
  - **Breaks tried**: each deliberate break and the test that caught it.
  - **Bugs**: the failing test, its output, and the ticket line it contradicts.
  - **Not tested**: what and why.
