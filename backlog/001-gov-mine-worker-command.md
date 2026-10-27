# 001: Start the worker with `gov-mine worker`

Spec: docs/specification/ (section 9, CLI; section 11, global concurrency cap)
Depends on: none

## What to build

A refactor with no change in what the worker does: a `gov-mine` command-line program exists, and `gov-mine worker [--concurrency N]` is the one way to start a worker. Alloy's `gov-mine-worker` script is removed.

## Acceptance criteria

- [x] `gov-mine --help` lists a `worker` command, and `gov-mine worker --help` documents `--concurrency`.
- [x] `gov-mine worker` starts a worker that registers the same tasks as before (including `jobs.retry_stalled`) and runs queued jobs.
- [x] `gov-mine worker --concurrency 3` runs at most three jobs at once; without the flag the configured default is used.
- [x] The `gov-mine-worker` script no longer exists, and `vp run dev` starts the worker through `gov-mine worker`.
- [x] An unknown command or option exits with a non-zero code.

## Out of scope

- Every other CLI command (002 onwards).

## Notes

- The CLI is Typer and follows Public Atlas's pattern: each command builds resources the way the API does and calls a service (decision 25). Commands are non-interactive, and later commands that print data take `--json`.
- Search docs and config for the old script name after removing it.
