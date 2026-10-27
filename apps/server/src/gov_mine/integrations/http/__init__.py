"""The crawler's HTTP client: httpx, one per process, opened by `build_resources`. Tests build
it over `httpx.MockTransport`."""

from importlib.metadata import version

import httpx

# The crawler's name: the product token robots.txt groups are matched against. A placeholder
# with no contact yet.
ROBOT_NAME = "my-bot"
# Sent on every request.
USER_AGENT = f"{ROBOT_NAME}/{version('gov-mine-server')}"
# Connect, read, write and pool wait, each.
TIMEOUT = httpx.Timeout(30.0)


def create_http_client(transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    """Redirects are not followed: where a redirect leads is the fence's decision, not the
    client's."""
    return httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        follow_redirects=False,
        http2=True,
        transport=transport,
    )


__all__ = ["ROBOT_NAME", "TIMEOUT", "USER_AGENT", "create_http_client"]
