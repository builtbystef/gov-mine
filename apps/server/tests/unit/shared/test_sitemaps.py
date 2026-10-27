from pathlib import Path

import pytest

from gov_mine.shared.sitemaps import Sitemap, parse_sitemap

CREATETO = Path(__file__).resolve().parents[3] / "fixtures" / "createto"


def test_the_saved_createto_index_points_to_its_one_sitemap():
    assert parse_sitemap((CREATETO / "sitemap.xml").read_bytes()) == Sitemap(
        pages=[], sitemaps=["https://createto.ca/sitemap-0.xml"]
    )


def test_the_saved_createto_sitemap_lists_232_pages_and_no_image_urls():
    sitemap = parse_sitemap((CREATETO / "sitemap-0.xml").read_bytes())

    assert sitemap.sitemaps == []
    assert len(sitemap.pages) == 232
    assert len(set(sitemap.pages)) == 232
    assert sitemap.pages[:3] == [
        "https://createto.ca",
        "https://createto.ca/contact-us",
        "https://createto.ca/news",
    ]


def test_a_sitemap_without_the_namespace_reads_the_same_and_trims_locations():
    body = b"""<urlset>
      <url><loc>
        https://example.org/a
      </loc></url>
      <url><lastmod>2026-01-01</lastmod></url>
      <url><loc>https://example.org/b</loc>
        <image:image xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
          <image:loc>https://example.org/b.png</image:loc>
        </image:image>
      </url>
    </urlset>"""

    assert parse_sitemap(body) == Sitemap(
        pages=["https://example.org/a", "https://example.org/b"], sitemaps=[]
    )


@pytest.mark.parametrize(
    "body",
    [
        b"<html><body>Not found</body></html>",
        b"<urlset><url><loc>https://example.org/",
        b"",
        b'<!DOCTYPE urlset [<!ENTITY a "x">]><urlset><url><loc>&a;</loc></url></urlset>',
    ],
    ids=["html", "truncated", "empty", "entities"],
)
def test_anything_but_a_sitemap_is_a_value_error(body: bytes):
    with pytest.raises(ValueError, match="not a sitemap"):
        parse_sitemap(body)
