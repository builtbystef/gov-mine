# 010: Refuse unsupported and oversized files

Spec: docs/specification/ (sections 4 UC-001, 5.4, 7 step 2, 11, 14 decisions 27 and 31)
Depends on: 004

## What to build

The crawler only downloads types it can store and parse, and nothing over 100 MB. It decides from the URL's extension before any request, and otherwise from the GET response's headers before reading the body. There is no HEAD request.

## Acceptance criteria

- [ ] A link with an unsupported extension (such as `.zip` or `.exe`) gets a `skipped_type` fetch and no request.
- [ ] A response whose `Content-Type` is unsupported is `skipped_type` and its body is not read.
- [ ] A response with `Content-Length` over 100 MB is `skipped_size` and its body is not read.
- [ ] A response without `Content-Length` whose body streams past 100 MB is dropped as `skipped_size`, and no snapshot is written.
- [ ] Supported types are HTML, PDF, office files (docx, xlsx, pptx and their older forms), csv, txt and images; each of them is fetched.
- [ ] A fetched page costs exactly one request: no HEAD is ever sent.
- [ ] The size cap is recorded in the run's `settings`.

## Out of scope

- Video and audio links, which become `youtube` documents (022).

## Notes

- Limits are user decisions (decision 31).
