# To do

## 1. Bootstrap from Alloy

- [x] Copy Alloy into `gov-mine` without `.git`, `node_modules` or `.venv`; keep
      `docs/specification/`; `git init`.
- [x] Rename `alloy` / `alloy_server` to `gov-mine` / `gov_mine`, and `ALLOY_*` to `GOV_MINE_*`.
- [x] Remove the auth, workspaces, CRM, assistant, mail, rate-limit and evals modules, their web
      features (`(auth)`, `(onboarding)`, the `[workspaceId]` segment, `features/*`) and their
      dependencies (`pwdlib`, `ai`, `@ai-sdk/react`, `streamdown`, `pydantic-evals`).
- [x] Add `typer`, `httpx[http2]`, `selectolax`, `markdownify`, `markitdown[all]` and
      `markitdown-ocr`.
- [x] Collapse the migrations into one fresh initial migration.
- [x] Done when `vp run ci` passes and `vp run dev` shows an empty app shell.

## 2. Capture fixtures

- [x] Save the CreateTO pages the spec relies on to `apps/server/fixtures/createto/`: the
      homepage, a project page with its `__NEXT_DATA__`, the Parkdale Hub page and its PDFs.
- [x] Save the MERX search tabs, tender pages and award panels to `apps/server/fixtures/merx/`.

## 3. Break the spec into tickets

- [x] Run `/spec-to-tickets docs/specification/README.md` and tell it the spec is every file
      the README links to.
- [x] Answer its gap questions; approve the ticket list and coverage table.
- [x] The thinnest end-to-end path (seed CreateTO, crawl one page, store a snapshot, show it on
      the run page) is ticket 002, after 001 replaces the `gov-mine-worker` script with
      `gov-mine worker`. The backlog is `backlog/001` to `backlog/057`.

## 4. Build

- [ ] For each ticket in `backlog/`: `/implement-ticket`, then `/review-ticket` and
      `/test-ticket`.

## Before the demo

- [ ] Deploy to Railway (web public; API and worker on the private network) and share the URL
      privately.
- [ ] Delete the Railway project after the demo.
