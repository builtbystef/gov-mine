# 11. Security and Privacy

- Sensitive data handled: public web pages only. `contact` records hold names, titles and work
  emails of public officials as published on the institution's own site.
- Who may see or change it: the developer, locally, and whoever is given the hosted demo's
  unlisted URL while it is up. No end users in phase 1.
- Retention and deletion: snapshots are append-only; bytes nothing cites may be pruned later
  (not built). A `contact` record whose person a page stops listing keeps its last state;
  removing it is out of scope in phase 1.
- Laws, regulations, or client rules that apply: only public pages and public files;
  robots.txt honoured; no login walls.
- Threats worth guarding against: SSRF via crawled links (private and link-local addresses are
  refused before DNS and after resolution); decompression bombs and oversized files (size caps,
  streaming); prompt injection from page content into the extractor (structured output with a
  fixed schema, no tool use, citations verified by code); accidental DDOS (per-host lock and
  delay, global concurrency cap); leaked keys (env only, `.env` gitignored).
