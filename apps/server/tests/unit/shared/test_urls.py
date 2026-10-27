import json
from pathlib import Path

import pytest

from gov_mine.shared.urls import find_links, is_within, looks_like_file, normalise_url

PROJECTS = Path(__file__).resolve().parents[3] / "fixtures" / "createto" / "projects"


def test_normalisation_makes_the_tickets_two_urls_one():
    assert (
        normalise_url("HTTPS://CreateTO.ca:443/projects/?utm_source=x#top")
        == normalise_url("https://createto.ca/projects")
        == "https://createto.ca/projects"
    )


@pytest.mark.parametrize(
    ("url", "normalised"),
    [
        ("http://createto.ca:80", "http://createto.ca/"),
        ("https://createto.ca", "https://createto.ca/"),
        ("https://createto.ca/", "https://createto.ca/"),
        ("https://createto.ca:8443/a/", "https://createto.ca:8443/a"),
        ("https://createto.ca/a?page=2&utm_medium=email&fbclid=1", "https://createto.ca/a?page=2"),
        ("https://createto.ca/a?gclid=1#x", "https://createto.ca/a"),
        ("https://createto.ca/A/b", "https://createto.ca/A/b"),
    ],
)
def test_normalisation(url: str, normalised: str):
    assert normalise_url(url) == normalised


@pytest.mark.parametrize("url", ["mailto:info@createto.ca", "/projects", "ftp://createto.ca/x"])
def test_only_absolute_http_urls_normalise(url: str):
    with pytest.raises(ValueError, match=r"."):
        normalise_url(url)


def test_is_within_a_prefix_goes_by_whole_path_segments():
    assert is_within("https://createto.ca/projects", "https://createto.ca/projects")
    assert is_within("https://createto.ca/projects/a", "https://createto.ca/projects")
    assert is_within("https://createto.ca/anything", "https://createto.ca/")
    assert not is_within("https://createto.ca/projects-archive", "https://createto.ca/projects")
    assert not is_within("http://createto.ca/projects", "https://createto.ca/projects")
    assert not is_within("https://www.createto.ca/projects", "https://createto.ca/projects")


def test_links_come_from_anchors_and_from_urls_anywhere_in_the_html():
    html = (
        '<html><head><base href="https://createto.ca/news/"></head><body>'
        '<a href="item#top">Item</a><a href="mailto:x@createto.ca">Mail</a>'
        '<a href="/projects/">Projects</a>'
        '<script>{"file":"https:\\/\\/a-us.storyblok.com\\/f\\/1\\/report.pdf"}</script>'
        "<p>See https://createto.ca/about.</p></body></html>"
    )

    assert find_links(html, "https://createto.ca/news/index") == [
        "https://createto.ca/news/item",
        "https://createto.ca/projects",
        # The base itself is a URL in the raw HTML.
        "https://createto.ca/news",
        "https://a-us.storyblok.com/f/1/report.pdf",
        "https://createto.ca/about",
    ]


def test_every_pdf_in_the_parkdale_hub_page_body_is_found():
    html = (PROJECTS / "parkdale-hub.html").read_text()
    files = json.loads((PROJECTS / "parkdale-hub-files" / "index.json").read_text())

    links = set(find_links(html, "https://createto.ca/projects/parkdale-hub"))

    assert len(files) == 14
    assert len([file for file in files if not file["in_rendered_html"]]) == 8
    assert {normalise_url(file["url"]) for file in files} <= links


@pytest.mark.parametrize(
    "url",
    [
        "https://a-us.storyblok.com/f/1017201/x/0a1b2c3d4e/report.pdf",
        "https://a-us.storyblok.com/f/1017201/1200x627/d41395f46b/annual-report-3-4.png",
        "https://example.com/Minutes.DOCX",
        "https://example.com/data/table.csv?download=1",
    ],
)
def test_a_url_with_a_file_extension_looks_like_a_file(url: str):
    assert looks_like_file(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://a-us.storyblok.com/about",
        "https://example.com/",
        "https://example.com/page.html",
        "https://example.com/report.pdf/view",
        "https://example.com/v1.2/notes",
        "https://example.com/?file=report.pdf",
        "https://a-us.storyblok.com/f/1017201/x/b500f5503f/createto_web_v2_h264.mp4",
    ],
)
def test_a_url_without_a_file_extension_does_not(url: str):
    assert not looks_like_file(url)
