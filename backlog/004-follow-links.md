# 004: Follow links breadth-first within the site

Spec: docs/specification/ (sections 3, 5.4, 7 steps 2–3, 10, 14 decision 31)
Depends on: 002

## What to build

A full run no longer stops at the homepage. Every URL found on an HTML page is normalised, recorded once as a webpage and fetched one link deeper, breadth-first, while it stays inside the institution's website prefix.

## Acceptance criteria

- [ ] URLs are taken both from `<a href>` tags and from anywhere else in the raw HTML (scripts, embedded JSON). On the saved Parkdale Hub page, all 14 PDFs in the page body are found, including the 8 that appear only in `__NEXT_DATA__`.
- [ ] URL normalisation lowercases scheme and host, drops default ports, fragments and tracking parameters, and treats trailing slashes the same way. `HTTPS://CreateTO.ca:443/projects/?utm_source=x#top` and `https://createto.ca/projects` normalise to the same URL.
- [ ] Each new normalised URL gets exactly one `webpages` row, with `discovered_from_webpage_id` set to the page it was first found on. A URL seen again gets no new row and no second fetch in the same run.
- [ ] A page found at depth d is fetched at depth d+1; a URL more than 50 links from a seed gets a `skipped_depth` fetch and no request.
- [ ] A URL on the institution's host but outside its website prefix, or on any other host, gets a `skipped_scope` fetch and no request.
- [ ] `run create --limit N` sends at most N requests in the run; jobs after that write no fetch row. The limit is recorded in `settings`.

## Out of scope

- The sitemap (005). Policies for other hosts, which until then are all `skipped_scope` (006). Type and size refusals (010).

## Notes

- Depth limit 50 and `--limit` semantics: decision 31 (user decision). Refused URLs don't count towards `--limit`.
- URL normalisation is one pure function, reused by the `text_hash` link list (015).
