"""The crawler's HTTP client: httpx, one per process, opened by `build_resources`. Tests pass a
client over `httpx.MockTransport` instead."""

from importlib.metadata import version

import httpx

# The crawler's name on every request. A placeholder with no contact yet.
USER_AGENT = f"my-bot/{version('gov-mine-server')}"
# Connect, read, write and pool wait, each.
TIMEOUT = httpx.Timeout(30.0)


def create_http_client() -> httpx.AsyncClient:
    """Redirects are not followed: where a redirect leads is the fence's decision, not the
    client's."""
    return httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        follow_redirects=False,
        http2=True,
    )


__all__ = ["TIMEOUT", "USER_AGENT", "create_http_client"]
