# 017: Read a snapshot's stated date

Spec: docs/specification/ (sections 3, 5.4, 8 parser port)
Depends on: 016

## What to build

When parsing, each snapshot records the latest date its content states about itself in its metadata: the later of its published (or created) and modified dates.

## Acceptance criteria

- [ ] A PDF with created date 2023-02-01 and modified date 2024-05-10 gets `stated_date = 2024-05-10`.
- [ ] An office file's core properties give its stated date the same way.
- [ ] A saved CreateTO project page gets the later of Storyblok's `published_at` and `updated_at` from `__NEXT_DATA__`.
- [ ] An HTML page with `article:published_time`/`article:modified_time` meta tags, or JSON-LD `datePublished`/`dateModified`, gets the later of the two.
- [ ] A snapshot with no date in its metadata has `stated_date` null.
