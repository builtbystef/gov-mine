---
name: audit-codebase
description: Runs a deep audit of a unit of the codebase (the whole repo, a directory, a branch, or a commit range) for refactoring and design cleanup opportunities, ranks them, and turns the ones the user accepts into backlog tickets. Reports only; changes no code.
argument-hint: "[path, commit range, branch, or nothing for the whole repo]"
disable-model-invocation: true
---

# Audit the codebase

Scope: $ARGUMENTS

Find the restructurings that would make this code markedly simpler to read and change, with behavior unchanged. Be ambitious: the best finding deletes whole branches, layers, or concepts; a refactor that only moves complexity around is not a finding. Be rigorous: every finding is verified against the code before it reaches the user.

## 1. Scope

- A path → that directory or file set. A commit range or branch (`a..b`, `main...HEAD`) → the files those commits touched, judged together with the modules around them, not as a diff. Nothing → the whole repo.
- Read `docs/decisions.md` if it exists. Don't re-raise anything it settles.

## 2. Map

- Gather the cheap signals first:
  - Size: `git ls-files <scope> | grep -E '\.(py|tsx?)$' | grep -vE '/generated/|/alembic/versions/' | xargs wc -l | sort -rn | head -30`
  - Churn: `git log --since='6 months ago' --format= --name-only -- <scope> | grep -E '\.(py|tsx?)$' | grep -v /generated/ | sort | uniq -c | sort -rn | while read -r n f; do [ -e "$f" ] && echo "$n $f"; done | head -30`
- Read the scope's entry points and module layout, and write a short map: each module, what it owns, and what it depends on. Large files with high churn are where problems cost the most; audit those hardest.
- For the whole repo, audit the hot spots in depth and the rest at the map level.

## 3. Hunt

- The lenses are in [lenses.md](lenses.md). Read it in full.
- Under ~2,000 lines in scope, do the hunt yourself. Above that, split the scope into at most four areas along module lines and give each to a subagent, all in parallel. Give each the area's paths, your map, the path to `lenses.md`, and these rules: read only, edit nothing, read callers outside the area when needed, and return candidates with `file:line` evidence.
- Then do the cross-cutting pass yourself, since no single area shows it: duplicated logic, the same decision made in several places, two ways to do one task, logic in the wrong layer. Search the whole repo for similar names and shapes.

## 4. Judge

For each candidate:

- **Verify it.** Re-read the cited code and trace the real callers. Raise each candidate's evidence as high as is cheap: pointed at the line → traced the call path → ran a script against the real code. Drop anything that rests on an unchecked claim.
- **Apply the deletion test.** If the target shape doesn't remove branches, layers, state, or concepts a reader must hold, drop it.
- **Drop the false positives:** problems that need inputs no caller sends; abstractions with only one way to vary (premature); "I'd have done it differently" without a concrete cost; patterns that match the codebase's own conventions.
- **Rank** by payoff (reader load removed, lines deleted, churn in the area) against cost (callers to migrate, test coverage to pin behavior first). Label each one **Strong**, **Worth exploring**, or **Speculative**.

Expect most raw candidates to fall out here. A short list you would defend line by line is the goal.

## 5. Report

Start with the map in a few lines, then the **top recommendation** and why it goes first. Then each candidate, ranked:

- **Title** and strength label
- **Where**: the files, with `file:line` evidence
- **Problem**: what a reader or changer pays for it today
- **Move**: the target shape, and what disappears
- **Payoff**, and **cost and risk**: the callers to migrate, and whether tests pin the behavior today
- **Keep it gone**: the lint rule, type, or test that stops it coming back, when one fits

End with a short **Considered and dropped** list, one line each, so the user sees what was ruled out.

## 6. Follow up

Ask which candidates to take forward.

- **Accepted** → write each as a ticket in `backlog/`, numbered after the highest existing one, in the format `spec-to-tickets` uses. Its acceptance criteria: behavior unchanged (existing tests pass unmodified, with characterization tests added first where coverage is missing); every caller migrated and the old path deleted, with no shim; the structural target stated so it can be checked (for example, "nothing outside `billing/` imports `billing/_rates`"); and the "keep it gone" check added where one fits.
- **Rejected for a lasting reason** → append one line to `docs/decisions.md` (create it if needed): the date, the candidate, and the reason, so later audits don't raise it again.
