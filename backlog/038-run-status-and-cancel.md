# 038: Check and cancel runs

Spec: docs/specification/ (sections 5.8, 7 step 7 and "Scheduler", 8, 9)
Depends on: 002

## What to build

The operator can see a run's status and cancel it. A cancelled run's remaining jobs do nothing. An institution can have only one active run at a time, whoever creates it.

## Acceptance criteria

- [ ] `gov-mine run status <id>` prints the run's status, trigger, start and finish times and error; `--json` prints the same.
- [ ] `gov-mine run cancel <id>` and `POST /runs/{id}/cancel` move a `queued` or `running` run to `cancelled`; cancelling a finished run returns an error and changes nothing.
- [ ] After cancelling, jobs of that run that start do nothing and write no rows; everything the run already wrote stays.
- [ ] Creating a second run for an institution with a `queued` or `running` run fails (409 from the API, non-zero exit from the CLI), and the database's partial unique index refuses it even if the check is bypassed.
