"""URLs as the crawl keys them: one normalised form per page, and the links a page holds."""

import html as html_entities
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

from selectolax.lexbor import LexborHTMLParser

DEFAULT_PORTS = {"http": 80, "https": 443}
# Query parameters that say how a visitor arrived, not what the page is. Any `utm_*` too.
TRACKING_PARAMETERS = frozenset(
    {"fbclid", "gclid", "dclid", "msclkid", "yclid", "igshid", "mc_cid", "mc_eid", "_ga", "_gl"}
)

# An absolute http(s) URL in running text: up to the first character a URL cannot hold.
_ABSOLUTE_URL = re.compile(r"""https?://[^\s"'<>\\^`{|}]+""", re.IGNORECASE)
# Punctuation that ends a sentence or a bracket rather than the URL.
_TRAILING = ".,;:!?)]"
# How JSON may write a slash.
_ESCAPED_SLASHES = ("\\/", "\\u002F", "\\u002f")


def normalise_url(url: str) -> str:
    """The one form a URL is stored and compared in: scheme and host lower-cased, the default
    port, the fragment and tracking parameters dropped, and no trailing slash (the root path is
    `/`). Raises `ValueError` for anything but an absolute http(s) URL."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    if scheme not in DEFAULT_PORTS:
        raise ValueError(f"not an http(s) URL: {url!r}")
    host = parts.hostname
    if not host:
        raise ValueError(f"no host: {url!r}")
    netloc = f"[{host}]" if ":" in host else host
    port = parts.port
    if port is not None and port != DEFAULT_PORTS[scheme]:
        netloc = f"{netloc}:{port}"
    userinfo = parts.netloc.rpartition("@")[0]
    if userinfo:
        netloc = f"{userinfo}@{netloc}"
    path = parts.path.rstrip("/") or "/"
    query = "&".join(
        pair for pair in parts.query.split("&") if pair and not _is_tracking(pair.split("=", 1)[0])
    )
    return urlunsplit((scheme, netloc, path, query, ""))


def _is_tracking(name: str) -> bool:
    name = name.lower()
    return name.startswith("utm_") or name in TRACKING_PARAMETERS


def is_within(url: str, prefix: str) -> bool:
    """Whether normalised `url` is `prefix` or below it: same scheme and host, and a path that
    is the prefix's or goes on from it at a `/`."""
    target, scope = urlsplit(url), urlsplit(prefix)
    if (target.scheme, target.netloc) != (scope.scheme, scope.netloc):
        return False
    base = scope.path.rstrip("/")
    return target.path == scope.path or target.path.startswith(f"{base}/")


def find_links(html: str, page_url: str) -> list[str]:
    """Every http(s) URL an HTML page holds, normalised, each once, in the order found: the
    `<a href>` targets resolved against the page (or its `<base href>`), then every absolute URL
    anywhere in the raw HTML, scripts and embedded JSON included. Some sites link files only
    there."""
    tree = LexborHTMLParser(html)
    base = page_url
    base_node = tree.css_first("base[href]")
    if base_node is not None and (base_href := base_node.attributes.get("href")):
        base = _join(page_url, base_href) or page_url
    found = [
        _join(base, href) for node in tree.css("a[href]") if (href := node.attributes.get("href"))
    ]
    raw = html_entities.unescape(html)
    for escaped in _ESCAPED_SLASHES:
        raw = raw.replace(escaped, "/")
    found += [match.group().rstrip(_TRAILING) for match in _ABSOLUTE_URL.finditer(raw)]
    links: dict[str, None] = {}
    for url in found:
        if url is None:
            continue
        try:
            links.setdefault(normalise_url(url))
        except ValueError:
            continue
    return list(links)


def _join(base: str, href: str) -> str | None:
    try:
        return urljoin(base, href.strip())
    except ValueError:
        return None


__all__ = ["DEFAULT_PORTS", "TRACKING_PARAMETERS", "find_links", "is_within", "normalise_url"]
