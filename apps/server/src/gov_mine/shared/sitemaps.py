"""Sitemaps (sitemaps.org): the page URLs a `<urlset>` lists, or the sitemap files a
`<sitemapindex>` points to."""

from dataclasses import dataclass
from xml.etree.ElementTree import Element

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError, fromstring


@dataclass(frozen=True)
class Sitemap:
    """What one sitemap file lists, as written in its `<loc>`s: pages, or other sitemaps."""

    pages: list[str]
    sitemaps: list[str]


def parse_sitemap(body: bytes) -> Sitemap:
    """The `<loc>` of every `<url>` of a `<urlset>`, or of every `<sitemap>` of a
    `<sitemapindex>`. Elements are matched by local name, so a sitemap without the
    sitemaps.org namespace reads the same. Raises `ValueError` for anything else, and for XML
    with a DTD's entities."""
    try:
        root = fromstring(body)
    except (ParseError, DefusedXmlException) as exc:
        raise ValueError(f"not a sitemap: {exc}") from exc
    match _local_name(root):
        case "urlset":
            return Sitemap(pages=_locations(root, "url"), sitemaps=[])
        case "sitemapindex":
            return Sitemap(pages=[], sitemaps=_locations(root, "sitemap"))
        case other:
            raise ValueError(f"not a sitemap: <{other}>")


def _locations(root: Element, entry_name: str) -> list[str]:
    found = []
    for entry in root:
        if _local_name(entry) != entry_name:
            continue
        for child in entry:
            if _local_name(child) == "loc" and child.text and child.text.strip():
                found.append(child.text.strip())
                break
    return found


def _local_name(element: Element) -> str:
    return str(element.tag).rpartition("}")[2]
