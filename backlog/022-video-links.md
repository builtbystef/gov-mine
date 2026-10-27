# 022: Turn video and audio links into youtube documents

Spec: docs/specification/ (sections 4 UC-001, 5.4)
Depends on: 010, 020

## What to build

Video and audio are never downloaded. A link to youtube.com, youtu.be or vimeo.com, or with a video or audio extension, is logged as skipped and kept as a `youtube` document of the run's institution.

## Acceptance criteria

- [ ] A link to `https://www.youtube.com/watch?v=abc` gets a `skipped_type` fetch with reason `video`, and no request is sent.
- [ ] That link becomes a `youtube` document of the run's institution, with no snapshot and no classification.
- [ ] Links to `youtu.be`, `vimeo.com`, and URLs ending in `.mp4` or `.mp3`, are handled the same way.
- [ ] Seeing the same video link again in a later run creates no second document.
