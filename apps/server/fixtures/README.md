# Fixtures

Saved copies of the CreateTO and MERX pages the spec relies on, captured 2026-10-27 by
`capture.py` (stdlib only; `python3 -I capture.py <out_dir> [createto] [merx]`). Plain user
agent `gov-mine-fixtures/0.1`, one request at a time, 1.5 s between requests per host, 5 s on
MERX (its `Crawl-delay`). Every saved body has a sibling `<name>.meta.json` with the URL,
status, response headers (ETag included), request headers and fetch time.

## createto/

- `robots.txt`, `sitemap.xml` (index), `sitemap-0.xml` (232 URLs).
- `homepage.html`.
- `procurement.html`: the page that links to the MERX search for "createto".
- `projects/dunn-house-phase-2.html` + `.next_data.json`: a typical project page and its
  extracted `__NEXT_DATA__`.
- `projects/parkdale-hub.html` + `.next_data.json`.
- `projects/parkdale-hub-files/`: the 14 PDFs in Parkdale Hub's own body. `index.json` marks
  which are also in the rendered HTML: 6 are, 8 appear only in `__NEXT_DATA__`. The page's
  raw HTML also embeds about 51 more PDF URLs from related initiatives; those were not kept.

## merx/

- `robots.txt`.
- `search/{open,closed,awarded}-page-N.html`: every page of each tab for `keywords=createto`.
  `summary.json` lists rows, distinct tenders and login-gated rows per tab.
- `tenders/open/`: the 1 open tender.
- `tenders/closed/`: 3 closed tenders that were not awarded.
- `tenders/awarded/<id>.html` + `<id>.award.js`: 10 awarded tenders and their award panels.
  The panel is fetched from the tender page's `data-ajax-url` with
  `X-Requested-With: XMLHttpRequest`; without that header MERX returns its welcome page.
  `0000186243` and `0000196314` are rosters with several awardees.

## Things the spec should know

- MERX pagination repeats rows: closed has 120 rows but 97 distinct, awarded 84 rows but 74
  distinct. Walking the pages does not reach every tender.
- 9 closed rows link to `/public/supplier/interception/view-notice/...`, not a tender page.
  They look login-gated and were not fetched.
- All 10 award panels say "Value Undisclosed"; no disclosed value was captured.
- The award panel needs the `X-Requested-With` header.
