# 056: Replay saved pages for the three variants

Spec: docs/specification/ (sections 4 UC-004, 5.7, 7 step 2, 12, 14 decision 32)
Depends on: 012, 016, 026

## What to build

`gov-mine dev replay --from fixtures/` serves the saved copies with one project page's phase changed and one PDF replaced by a corrupt file. `run create --replay <address>` runs against that server, so the unchanged, changed and failed variants can be shown without the live site changing.

## Acceptance criteria

- [x] `gov-mine dev replay --from fixtures/` serves every saved URL, whatever its host, with the edited project page and the corrupt PDF.
- [x] A run created with `--replay <address>` sends every request to that address, passes the private-address check for it, and records `replay` and the address in `settings`.
- [x] A URL outside the saved set gets `skipped_scope` with reason `not_in_replay`, and no webpage is marked missing.
- [ ] After a live-like run of the saved set, a replay run's report shows one amended project record and one failed snapshot, and `gov-mine records history <id>` shows the phase change.
      (Partly: after an `--as-saved` replay, the variant replay writes exactly two snapshots, the edited Dunn House page (`ready`) and the corrupt PDF (`failed`). The amended record, the report and `records history` wait for extraction (023), the report and the records CLI (026).)
- [ ] Running the replay twice in a row, the second report shows zero snapshots and zero paid calls.
      (Partly: the second variant replay writes zero snapshots. Zero paid calls and the report wait for extraction (023) and the report.)

## Notes

- Section 12 asks for one end-to-end test that crawls the replay server and asserts the report; this ticket's criteria are its source.
