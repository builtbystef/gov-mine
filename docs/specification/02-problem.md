# 2. Problem

- Problem: companies that sell to governments need to know, for tens of thousands of public
  bodies, what each one is planning, buying and announcing, with a link back to the page that
  says so, kept current as sites change. Each
  institution's site is different, documents move between HTML and PDF, and files sit on other
  hosts. A hand-written scraper per site does not scale, and a model reading every page on
  every run does not pay.
- Desired outcome and signs of success:
  - One command crawls createto.ca from the homepage, exhaustively, politely, and keeps every
    page and linked file, including files on other hosts.
  - Typed records with location, phase, dates and so on, each field with the page, page number
    and an excerpt that code has checked is really there.
  - A second, unchanged run costs requests and no model calls; a changed page produces a new
    document version and a new record state; a failed file is visible as such.
  - A run report with time, requests, files processed, records, paid calls and cost, computed
    from the logs rather than counted by hand.
  - The same design applies to any institution by adding a row, not code; a rule extractor is
    added when a page family is worth it.
