# 005: Seed the frontier from the sitemap

Spec: docs/specification/07-behaviour.md (step 1)
Depends on: 004

## What to build

When a full run starts, it reads the host's `sitemap.xml`, if there is one, and seeds the crawl with every URL it lists, alongside the homepage.

## Acceptance criteria

- [ ] On a full run of the saved CreateTO site, every URL in `sitemap.xml` and the sitemap files it links to (`sitemap-0.xml`) is fetched at depth 0.
- [ ] A host with no sitemap (404) still runs from the homepage, and the run finishes normally.
- [ ] A sitemap URL also found as a link is fetched only once.
