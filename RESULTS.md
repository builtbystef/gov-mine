# Results

<!-- Every number below comes from `uv run gov-mine run report <run id>` on 2026-10-27. -->

gov-mine crawls CreateTO from its homepage. It keeps a copy of every page and
linked file, including files on other hosts. A model classifies each page and
extracts typed records from the documents. Every field of a record carries a
citation: the page or file link, the PDF page, and a short excerpt checked
against the source text. Results are exported as JSON Lines for other
services, and a re-run only pays for what changed.

- Run instructions: [README.md](README.md#running-it)
- Design: [docs/specification/](docs/specification/README.md)
- Example output: [examples/](examples/)

## How these results were produced

```sh
vp run dev                                    # API, worker (GOV_MINE_JOBS_CONCURRENCY=8), dashboard
cd apps/server
uv run gov-mine seed                          # CreateTO's institution id
uv run gov-mine run create <id> --full        # run 1, then again for run 2
uv run gov-mine run report <run id>
uv run gov-mine export --out ../../examples/run-1
```

Machine: AMD Ryzen 5 3600 (6 cores, 12 threads), 15 GB RAM, home broadband. Date:
2026-10-27. Model access: OpenRouter. The database and bucket were emptied before run 1.

Two bugs surfaced during run 1 and were fixed while it ran (commit `2646198`, with a test):

- **A CDN's images held back its PDFs.** Every CreateTO page links a dozen resized copies of
  each image on `a-us.storyblok.com`, the same host as its PDFs. Each was queued behind the
  host's lock only to be refused without a request, so the queue drained at 2 jobs a second.
  Fetches the fence will refuse are now queued without the lock: 70 a second.
- **PDFium is not thread-safe.** Parses run in worker threads; 57 sound PDFs failed with
  "Data format error" when parsed in parallel. Splitting a PDF into pages now holds a lock.
  The 57 were parsed again within run 1, and all succeeded.

From 11:37 a second worker (12 job slots) shared the queue, to get through the model calls.

## Two runs of the live site

Run 1 is the first full crawl. Run 2 is a second full crawl right after it, of
a site that hasn't changed.

|                                     |           Run 1 (first) | Run 2 (unchanged repeat) |
| ----------------------------------- | ----------------------: | -----------------------: |
| Run id                              |         `01a17def-b8eb` |          `01a17e06-2748` |
| Time taken                          |             24 min 23 s |               7 min 43 s |
| Requests sent                       |                     722 |                      722 |
| Snapshots written (new bytes)       |            709 (1.1 GB) |                        0 |
| Files processed                     | 709 (466 PDF, 243 HTML) |        0 (709 unchanged) |
| Files failed                        |                       0 |                        0 |
| Documents new / changed             |                 676 / 0 |                    0 / 0 |
| Records created / amended           |                 710 / 2 |                    0 / 0 |
| Paid calls                          |                   1,323 |                        0 |
| Cost, reported by OpenRouter        |                   $0.47 |                       $0 |
| Cost, estimated from the price list |                   $0.44 |                       $0 |

Run 2 sent the same 722 requests and got the same bytes back for all 709 pages and files, so
it wrote nothing and called no model. It took a third of run 1's time: the requests, at one a
second per host, are what is left. Conditional requests (ETag, postponed) would make most of
them 304s.

Why run 2 costs nothing: a page whose bytes are unchanged writes no snapshot, so
it isn't parsed, classified or extracted again. A page whose bytes change but
whose text doesn't (a new build id, say) is parsed but not re-extracted.

<details>
<summary>Run 1: full report</summary>

| Number                              | Value                                                           |
| ----------------------------------- | --------------------------------------------------------------- |
| Run                                 | 01a17def-b8eb-77e4-a3a3-9c94d718df6c (CreateTO, full, finished) |
| Time taken                          | 1462.9 s                                                        |
| Requests sent                       | 722                                                             |
| Snapshots written                   | 709                                                             |
| Files processed                     | 709                                                             |
| Files failed                        | 0                                                               |
| Files still parsing                 | 0                                                               |
| Documents new                       | 676                                                             |
| Documents changed                   | 0                                                               |
| Documents removed                   | 0                                                               |
| Records created                     | 710                                                             |
| Records amended                     | 2                                                               |
| Paid calls                          | 1323                                                            |
| Cost, estimated from the price list | $0.439195                                                       |
| Cost, reported by OpenRouter        | $0.474580                                                       |

| Fetch outcome  | Fetches | Requests sent |
| -------------- | ------: | ------------: |
| blocked_robots |       3 |             0 |
| failed_http    |      13 |            13 |
| fetched        |     709 |           709 |
| skipped_scope  |    6597 |             0 |

| Paid calls by purpose | Calls | Input tokens | Output tokens | Estimated (price list) | Reported (OpenRouter) |
| --------------------- | ----: | -----------: | ------------: | ---------------------: | --------------------: |
| classify              |   709 |      2787195 |        210600 |              $0.117062 |             $0.117062 |
| extract               |   614 |      1717125 |        300841 |              $0.322133 |             $0.357517 |

| Cost by provider | Calls | Estimated (price list) | Reported (OpenRouter) | Calls with no reported cost |
| ---------------- | ----: | ---------------------: | --------------------: | --------------------------: |
| openrouter       |  1323 |              $0.439195 |             $0.474580 |                           0 |

Removed documents (webpage went missing in this run):

- none

Unextracted documents (extraction failed):

- none

Fallback reasons per source:

- none: no_rule 544
- 01a17def-d1f1-7146-8d06-2dc191809702: no_rule 1
- 01a17df0-1bf6-7160-b720-d1b08575b9d5: no_rule 16
- 01a17df0-2929-71fc-a031-bdd309d81dc2: no_rule 10
- 01a17df0-35fc-7700-b696-2d5fda3b26f0: no_rule 3
- 01a17df0-3c47-728f-ba06-ad7f7cca1e18: no_rule 39

</details>

<details>
<summary>Run 2: full report</summary>

| Number                              | Value                                                           |
| ----------------------------------- | --------------------------------------------------------------- |
| Run                                 | 01a17e06-2748-730d-879a-83363923ad39 (CreateTO, full, finished) |
| Time taken                          | 463.2 s                                                         |
| Requests sent                       | 722                                                             |
| Snapshots written                   | 0                                                               |
| Files processed                     | 0                                                               |
| Files failed                        | 0                                                               |
| Files still parsing                 | 0                                                               |
| Documents new                       | 0                                                               |
| Documents changed                   | 0                                                               |
| Documents removed                   | 0                                                               |
| Records created                     | 0                                                               |
| Records amended                     | 0                                                               |
| Paid calls                          | 0                                                               |
| Cost, estimated from the price list | $0.000000                                                       |
| Cost, reported by OpenRouter        | none reported                                                   |

| Fetch outcome  | Fetches | Requests sent |
| -------------- | ------: | ------------: |
| blocked_robots |       3 |             0 |
| failed_http    |      13 |            13 |
| skipped_scope  |    6597 |             0 |
| unchanged      |     709 |           709 |

| Paid calls by purpose | Calls | Input tokens | Output tokens | Estimated (price list) | Reported (OpenRouter) |
| --------------------- | ----: | -----------: | ------------: | ---------------------: | --------------------: |

| Cost by provider | Calls | Estimated (price list) | Reported (OpenRouter) | Calls with no reported cost |
| ---------------- | ----: | ---------------------: | --------------------: | --------------------------: |

Removed documents (webpage went missing in this run):

- none

Unextracted documents (extraction failed):

- none

Fallback reasons per source:

- none

</details>

### Blocked and skipped links

Every refused link is logged as a `fetches` row with an outcome and a reason.
The run page's Fetches tab filters by outcome.

| Outcome                          |  Run 1 | Typical reasons                                                                 |
| -------------------------------- | -----: | ------------------------------------------------------------------------------- |
| `skipped_scope`                  |  6,597 | `not_a_file` (a page on a files-only host), `outside_prefix`, `private_address` |
| `skipped_type`                   |      0 | `extension png`, `content_type application/json`                                |
| `skipped_size`                   |      0 | over 100 MB                                                                     |
| `skipped_depth`                  |      0 | more than 50 links from a seed                                                  |
| `blocked_robots`                 |      3 | `disallowed` by robots.txt                                                      |
| `failed_http` / `failed_timeout` | 13 / 0 | 4xx; 5xx or timeout after 3 retries                                             |

In run 1:

- `skipped_scope`: 6,380 of the 6,597 are resized images on CreateTO's asset CDN
  (`…/photo.jpg/m/640x474/smart`); the rest are pages on other hosts (toronto.ca, YouTube,
  Outlook safe links), which are `files_only`. All are refused without a request.
- `blocked_robots`: two brochures on `f.datasrvr.com` and one Dropbox file.
- `failed_http`: 9 redirects (307/308, see known gaps), 3 not found, 1 forbidden.
- 6 hosts were fetched from: `a-us.storyblok.com` 438, `createto.ca` 243, `www.toronto.ca`
  22, `www.waterfrontoronto.ca` 4, `pnlt.ca` 1, `ontarioplanners.ca` 1.

## Variants: unchanged, changed source, failed file

Saved local copies, served by a replay server, so the variants don't depend on
the live site changing:

```sh
cd apps/server
uv run gov-mine dev replay --from fixtures/ --as-saved   # the copies as saved
uv run gov-mine run create <id> --full --replay http://127.0.0.1:8765
# stop it, then serve the variants: Dunn House's phase changed, one Parkdale Hub PDF corrupted
uv run gov-mine dev replay --from fixtures/
uv run gov-mine run create <id> --full --replay http://127.0.0.1:8765   # changed source + failed file
uv run gov-mine run create <id> --full --replay http://127.0.0.1:8765   # unchanged
```

| Variant                      | Run id          | What happened                                                                                  | Snapshots | Records amended | Files failed | Paid calls |    Cost |
| ---------------------------- | --------------- | ---------------------------------------------------------------------------------------------- | --------: | --------------: | -----------: | ---------: | ------: |
| Baseline (as saved)          | `01a17e0d-48b7` | 18 requests. 17 copies matched run 2's bytes; Dunn House, a redirect on the live site, was new |         1 |   0 (1 created) |            0 |          2 | $0.0011 |
| Changed source + failed file | `01a17e12-aef8` | Dunn House's phase moved on; one Parkdale Hub PDF served corrupt, kept with its parse error    |         2 |               1 |            1 |          1 | $0.0008 |
| Unchanged                    | `01a17e13-5147` | Same 18 requests, same bytes                                                                   |         0 |               0 |            0 |          0 |      $0 |

Each replay run took 38 s. The URLs the replay server does not hold (788 links) are logged as
`skipped_scope` `not_in_replay`, without a request.

The amended record's history, from `record_snapshots` (and `/records/01a17e0d-c48a-7750-8ee3-c07f4302e1dd`
in the dashboard):

| `created_at` (UTC)  | name         | phase                     |
| ------------------- | ------------ | ------------------------- |
| 2026-10-27 15:49:53 | Spring House | Pre-construction          |
| 2026-10-27 15:55:47 | Spring House | Delivery and Construction |

The corrupt PDF (`backgroundfile-101969.pdf`, 51 bytes served) got a new snapshot with
`text_status = failed` and PDFium's message in `text_error`. Its bytes are kept, it is not
retried, and the record extracted from its earlier, sound version (84,893 bytes) stays
current: a failed file does not erase what was known.

## Example output

`gov-mine export --out <dir>` writes one JSON Lines file per record type
(`projects.jsonl`, `news_items.jsonl`, `rfps.jsonl`, …), plus
`documents.jsonl`, `citations.jsonl` and `manifest.json`. Only records dated
within the last five years are kept; undated ones are kept too. Exporting the
same database twice gives the same lines.

- Run 1's export: [examples/run-1/](examples/run-1/)
- Records per type, dated 2021-10-27 or later (480 of the 710 created): 155 projects,
  195 meetings, 95 contacts, 34 news items, 1 RFP; 0 contracts and 0 grants. 1,501
  citations, every one with a page number; 1,438 (95.8%) verified against the page text.

A project record and two of its citations (abridged: it has 7 citations, one per field):

```json
{
  "id": "01a17e04-3f1a-7517-bcc2-76a79b1374d7",
  "institution": "CreateTO",
  "document": "https://a-us.storyblok.com/f/1017201/x/505dcf904a/resource-2021-report-completion-of-phase-2-feasibility-study-advancing-to-phase-3.pdf",
  "key": "",
  "name": "Parkdale Hub Project",
  "phase": "Phase 2 feasibility study completed; advancing to Phase 3",
  "end_date": null,
  "location": "Parkdale, at 1303 and 1313 Queen Street West and 220 Cowan Avenue",
  "partners": [
    "Parks, Forestry & Recreation",
    "Toronto Public Library",
    "Housing Secretariat",
    "…"
  ],
  "materials": null,
  "start_date": "2017-01-01",
  "description": "A transformational city-building initiative intended to deliver wide-ranging benefits to the Parkdale community.",
  "citations": [
    {
      "field": "location",
      "url": "https://a-us.storyblok.com/f/1017201/x/505dcf904a/resource-2021-report-completion-of-phase-2-feasibility-study-advancing-to-phase-3.pdf",
      "page": 5,
      "excerpt": "City-owned properties located at 1303, 1313 Queen St. W. and 220 Cowan Ave., in the heart of the Parkdale community.",
      "verified": true
    },
    {
      "field": "name",
      "url": "https://a-us.storyblok.com/f/1017201/x/505dcf904a/resource-2021-report-completion-of-phase-2-feasibility-study-advancing-to-phase-3.pdf",
      "page": 1,
      "excerpt": "Parkdale Hub Project – Completion of Phase 2 Feasibility Study, Advancing to Phase 3",
      "verified": true
    }
  ],
  "first_seen_at": "2026-10-27T15:39:29.947010+00:00",
  "last_changed_at": "2026-10-27T15:39:30.172848+00:00"
}
```

## Costs

All model costs are per run and come from the `ai_calls` ledger. Two figures
are kept for every call: the cost OpenRouter **reported**, and an **estimate**
from our price list (`apps/server/src/gov_mine/modules/ledger/prices.py`,
version 2026-10-27).

| Model               | Used for                           | Price list (USD per 1M tokens, input / output) | Run 1                                 | Per call (reported) |
| ------------------- | ---------------------------------- | ---------------------------------------------- | ------------------------------------- | ------------------: |
| `typesafe/jev-1.14` | Classifying each new page          | 0.042 / free                                   | 709 calls, 2.8M tokens in, $0.117     |            $0.00017 |
| `openai/gpt-6-luna` | Extracting records from a document | 0.10 / 0.50                                    | 614 calls, 1.7M in / 0.3M out, $0.358 |            $0.00058 |

OpenRouter reported 11% more than the price list for `gpt-6-luna` on run 1 ($0.358 against
$0.322) and the same for Jev. The reported figure is the one to budget with. A full first
crawl of CreateTO costs about **$0.47** in model calls: about $0.0007 per document.

No other paid service is called: no search API, no OCR service, no proxy.

### Monthly running cost on Railway (ESTIMATE)

These are estimates from stated assumptions, not quotes. Railway bills usage per second
(2026-10-27 price page: $10 per GB of memory a month, $20 per vCPU a month, $0.15 per GB of
volume a month, $0.015 per GB a month in buckets), on top of a plan: Hobby is $5 with $5 of
usage included, Pro $20 with $20 included.

Assumptions: one full run of CreateTO a week; the four images of the Deploying table (API,
worker, dashboard, plus Railway's PostgreSQL); snapshots in a Railway bucket. Memory is what
the processes used here: the worker reached 0.9 to 1.5 GB while parsing large PDFs, the API
about 50 MB, the dashboard about 160 MB, PostgreSQL about 300 MB.

| Item                     | Basis                                                                           | Estimate per month |
| ------------------------ | ------------------------------------------------------------------------------- | -----------------: |
| Model calls, first run   | Run 1's reported cost, once                                                     |        $0.47, once |
| Model calls, weekly runs | Run 2 cost $0; plus changed documents, say 5% a week at run 1's $0.0007 each    |             ~$0.10 |
| Worker                   | ~1 GB held between runs (Python keeps what parsing took), ~0.05 vCPU on average |        ~$11 (est.) |
| API and dashboard        | ~0.25 GB together, near-idle CPU                                                |      ~$2.50 (est.) |
| PostgreSQL               | ~0.3 GB memory, 1 GB volume                                                     |      ~$3.20 (est.) |
| Bucket                   | 1.1 GB of snapshots and their text after run 1, growing only with changed files |      ~$0.02 (est.) |
| **Total**                | About $17 of usage: on the Pro plan, its $20 minimum                            |  **$15–25 (est.)** |

Hosting dominates: model calls are cents a month once the first crawl is paid for. The same
app serves more institutions for little more than their first crawl, until one worker is no
longer enough.

Snapshot storage after run 1: `SELECT pg_size_pretty(sum(size_bytes)) FROM webpage_snapshots;`
gives 1104 MB (709 snapshots: 466 PDFs, 243 HTML pages).

## Decisions and trade-offs

- **Being polite comes first:** one request at a time per host, at least 1 s
  apart, or the host's `Crawl-delay` if longer. robots.txt is honoured for `*`
  and for our user agent. Private addresses are refused. Links found within
  pages are followed up to 50 deep.
- **Files on other hosts:** a host seen for the first time is `files_only`.
  Its files (PDF, office, CSV) are fetched but its pages are not crawled.
- **Two models, each used for one job:** Jev classifies pages cheaply as a
  listing, a document or neither. Only documents go to the extraction model.
- **Citations are checked, not trusted:** each excerpt is searched for on the
  cited page. A miss is kept but marked `verified=false`.
- **History, not overwrites:** a changed field adds a record snapshot. Earlier
  values and when they were extracted stay queryable.
- **Re-runs only pay for change:** byte hash, then text hash, then
  re-extraction, as described under the two runs.
- **Images are not downloaded:** they need OCR, which was postponed.

## Postponed, and why

The spec in `docs/specification/` covers more than one day allowed. Postponed:
OCR for scanned PDFs, the MERX procurement platform, scheduled and incremental
runs, conditional requests (ETag), rule-based extractors, a review queue for
low-confidence items, and the settings and domains pages. Also cut on the day:
CLI commands to list runs and records, and automated checks of the amended record in the
replay test (the variants below were checked by hand).

## Known gaps

- DNS rebinding: an address is checked when the name is resolved, and the HTTP
  client resolves it again when it connects.
- Redirects were not followed during these runs: a 3xx was recorded as `failed_http`. In
  run 1, 9 createto.ca URLs redirected, among them `/projects/dunn-house-phase-2` (now
  `/springhouse`) and the news topic pages (now `/news?topic=…`); a target was crawled only
  when another page linked it (`/news` was, `/springhouse` was not). Fixed after the runs
  (commit `b8d8dba`, with a test), so that run 2 stayed an unchanged repeat: a redirect is
  still `failed_http`, with `redirect <target>` as its reason, and the target is queued
  like a link found on the page.
- robots.txt is applied for both `*` and our user agent's group, which is
  stricter than RFC 9309.
- No `stated_date` parser yet: document dates come from the model's extraction.
- An image on a files-only host is refused as `not_a_file`, not `skipped_type`: right
  outcome, vaguer reason.
- The worker keeps the memory it took to parse the largest PDFs (1.5 GB here). Parsing in a
  child process per file would hand it back.
- A crawl test (`…seeds_every_url_of_the_saved_createto_sitemap_at_depth_0`) is flaky under
  load and passes alone.
