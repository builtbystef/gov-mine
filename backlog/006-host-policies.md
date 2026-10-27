# 006: Apply host policies to other hosts

Spec: docs/specification/05-data-model.md (section 5.4, `domains`)
Depends on: 004

## What to build

Links to hosts other than the institution's own are handled by each host's `crawl_policy`. A host seen for the first time becomes `files_only`: its files are downloaded but its pages' links are not followed. A `blocked` host is never fetched.

## Acceptance criteria

- [x] A link to a host never seen before creates a `domains` row with policy `files_only`.
- [x] On a `files_only` host, a link that looks like a file (for example `https://a-us.storyblok.com/f/…/report.pdf`) is fetched, and a link that looks like a page is `skipped_scope`.
- [x] Links found inside a file fetched from a `files_only` host are not enqueued.
- [x] Every link to a `blocked` host gets a `skipped_scope` fetch and no request.
- [x] Changing a host's policy from `files_only` to `crawl` makes the next run follow its in-scope links.

## Out of scope

- The `platform` policy (035). The Domains page for editing policies (050).

## Notes

- "Looks like a file" is decided from the URL's extension, using the same known-extension list as the type fence (010).
