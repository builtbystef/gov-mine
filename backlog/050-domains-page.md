# 050: Edit host policies on the Domains page

Spec: docs/specification/ (sections 4 UC-007, 9 Domains)
Depends on: 006, 007

## What to build

A Domains page lists every host with its policy, delay and robots status, and lets the operator change a host's policy.

## Acceptance criteria

- [ ] `GET /domains` returns a limit/offset page of hosts with name, policy, `crawl_delay_ms` and when robots.txt was fetched; the Domains page shows them.
- [ ] Changing a host's policy on the page saves it through `PATCH /domains/{id}`, and the next run applies it.
- [ ] A policy outside `crawl`, `files_only`, `platform` and `blocked` is refused with 422.
