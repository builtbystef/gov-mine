# 009: Refuse private addresses

Spec: docs/specification/ (sections 7 step 2, 11, 14 decision 38)
Depends on: 004

## What to build

The crawler never requests a private, loopback or link-local address, whether the URL names it directly or a hostname resolves to one.

## Acceptance criteria

- [x] A link to `http://127.0.0.1/`, `http://10.0.0.5/`, `http://192.168.1.1/` or `http://169.254.169.254/` gets a `skipped_scope` fetch with reason `private_address` and no request.
- [x] A link whose hostname resolves to a private address gets the same refusal, and no connection is made.
- [x] A link to an IPv6 loopback or link-local address (`http://[::1]/`, `http://[fe80::1]/`) is refused the same way.
- [x] The private-address check is the first check in the fence: a private address on a `blocked` host is reported as `private_address`.

## Out of scope

- The replay server's exemption (056).

## Notes

- Outcome `skipped_scope` with reason `private_address` is a user decision (decision 38).
