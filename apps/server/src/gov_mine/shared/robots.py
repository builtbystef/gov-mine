"""robots.txt (RFC 9309), read for two groups: `*` and the crawler's own name. A URL is allowed
only when both allow it, and the delay asked for is the longer of the two."""

from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from protego import Protego

ROBOTS_PATH = "/robots.txt"
ANY_AGENT = "*"


def robots_url(url: str) -> str:
    """The robots.txt that governs `url`: the one at the root of its scheme, host and port."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, ROBOTS_PATH, "", ""))


def robots_allows(robots_txt: str, url: str, agent: str) -> bool:
    """Whether neither the `*` group nor `agent`'s group of `robots_txt` disallows `url`. A
    group that does not exist allows everything, so an empty file allows every path."""
    rules = _parse(robots_txt)
    return rules.can_fetch(url, ANY_AGENT) and rules.can_fetch(url, agent)


def robots_crawl_delay(robots_txt: str, agent: str) -> float | None:
    """The longer `Crawl-delay` of the `*` group and `agent`'s, in seconds, or None."""
    rules = _parse(robots_txt)
    delays = [d for a in (ANY_AGENT, agent) if (d := rules.crawl_delay(a)) is not None]
    return max(delays, default=None)


@lru_cache(maxsize=64)
def _parse(robots_txt: str) -> Protego:
    return Protego.parse(robots_txt)


__all__ = ["ROBOTS_PATH", "robots_allows", "robots_crawl_delay", "robots_url"]
