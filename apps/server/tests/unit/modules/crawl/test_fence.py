import asyncio
import socket
from ipaddress import ip_address
from urllib.parse import urlsplit

import httpx
import pytest

from gov_mine.modules.crawl import service
from gov_mine.modules.crawl.models import CrawlPolicy, FetchOutcome
from gov_mine.modules.crawl.service import (
    MAX_FILE_BYTES,
    address_refusal,
    read_body,
    refusal,
    response_refusal,
    type_refusal,
)
from gov_mine.shared.addresses import IPAddress

WEBSITE = "https://createto.ca/"
REPORT = "https://a-us.storyblok.com/f/1017201/x/0a1b2c3d4e/report.pdf"


@pytest.mark.parametrize(
    ("url", "policy", "depth", "refused"),
    [
        ("https://createto.ca/projects", CrawlPolicy.CRAWL, 1, None),
        (REPORT, CrawlPolicy.FILES_ONLY, 1, None),
        ("https://a-us.storyblok.com/about", CrawlPolicy.FILES_ONLY, 1, "not_a_file"),
        (REPORT, CrawlPolicy.BLOCKED, 1, "blocked_host"),
        ("https://tracker.example/", CrawlPolicy.BLOCKED, 0, "blocked_host"),
        ("https://www.merx.com/", CrawlPolicy.PLATFORM, 1, "platform_host"),
        # Another host set to crawl is in scope whole: the prefix bounds only the website's host.
        ("https://docs.example/guide", CrawlPolicy.CRAWL, 1, None),
        ("http://createto.ca/projects", CrawlPolicy.CRAWL, 1, "outside_prefix"),
    ],
)
def test_the_host_policy_decides_scope(
    url: str, policy: CrawlPolicy, depth: int, refused: str | None
):
    expected = None if refused is None else (FetchOutcome.SKIPPED_SCOPE, refused)
    assert refusal(url, policy, WEBSITE, depth) == expected


def test_a_file_on_a_files_only_host_is_still_bounded_by_depth():
    assert refusal(REPORT, CrawlPolicy.FILES_ONLY, WEBSITE, 51) == (
        FetchOutcome.SKIPPED_DEPTH,
        "depth 51 > 50",
    )


PRIVATE = (FetchOutcome.SKIPPED_SCOPE, "private_address")
DNS = {
    "createto.ca": ["93.184.215.14"],
    "intranet.example": ["10.1.2.3"],
    "metadata.example": ["169.254.169.254"],
    "dual.example": ["93.184.215.14", "fd12::1"],
    "v6.example": ["2606:4700::1"],
}


@pytest.fixture
def dns(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The fence's DNS, faked from `DNS`; the hosts it was asked for."""
    asked: list[str] = []

    async def resolve(host: str) -> list[IPAddress]:
        asked.append(host)
        if host not in DNS:
            raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
        return [ip_address(address) for address in DNS[host]]

    monkeypatch.setattr(service, "resolve", resolve)
    return asked


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://169.254.169.254/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[::ffff:10.0.0.1]/",
        "http://0.0.0.0/",
    ],
)
def test_a_url_naming_a_private_address_is_refused_before_any_dns(url: str, dns: list[str]):
    assert asyncio.run(address_refusal(url)) == PRIVATE
    assert dns == []


@pytest.mark.parametrize(
    ("url", "refused"),
    [
        ("https://intranet.example/report.pdf", PRIVATE),
        ("http://metadata.example/latest/meta-data", PRIVATE),
        # Any one private address is enough: the connection could go to it.
        ("https://dual.example/", PRIVATE),
        ("https://createto.ca/projects", None),
        ("https://v6.example/", None),
        # A name that does not resolve is left to fail when requested.
        ("https://nowhere.example/", None),
    ],
)
def test_a_host_name_is_refused_when_it_resolves_to_a_private_address(
    url: str, refused: tuple[FetchOutcome, str] | None, dns: list[str]
):
    assert asyncio.run(address_refusal(url)) == refused
    assert dns == [urlsplit(url).hostname]


def test_a_public_address_written_out_is_not_refused(dns: list[str]):
    assert asyncio.run(address_refusal("https://8.8.8.8/report.pdf")) is None
    assert asyncio.run(address_refusal("https://[2606:4700::1]/")) is None
    assert dns == []


def test_localhost_is_refused_through_the_system_resolver():
    assert asyncio.run(address_refusal("http://localhost:8000/")) == PRIVATE


@pytest.mark.parametrize(
    ("url", "refused"),
    [
        ("https://createto.ca/files/archive.zip", (FetchOutcome.SKIPPED_TYPE, "extension zip")),
        ("https://createto.ca/setup.exe", (FetchOutcome.SKIPPED_TYPE, "extension exe")),
        ("https://createto.ca/projects", None),
        ("https://createto.ca/news.aspx", None),
        (REPORT, None),
    ],
)
def test_an_unsupported_extension_is_refused_before_any_request(
    url: str, refused: tuple[FetchOutcome, str] | None
):
    assert type_refusal(url) == refused


def response(content_type: str | None = None, content_length: int | None = None) -> httpx.Response:
    headers = {"Content-Type": content_type, "Content-Length": content_length}
    return httpx.Response(200, headers={k: str(v) for k, v in headers.items() if v is not None})


# 100 MB, as decision 31 sets it.
assert MAX_FILE_BYTES == 100 * 1024 * 1024


@pytest.mark.parametrize(
    ("url", "content_type"),
    [
        ("https://createto.ca/projects", "text/html; charset=utf-8"),
        ("https://createto.ca/projects", "application/xhtml+xml"),
        ("https://createto.ca/download/1", "application/pdf"),
        ("https://createto.ca/download/2", "application/msword"),
        (
            "https://createto.ca/download/3",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("https://createto.ca/download/4", "application/vnd.ms-excel"),
        (
            "https://createto.ca/download/5",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        ("https://createto.ca/download/6", "application/vnd.ms-powerpoint"),
        (
            "https://createto.ca/download/7",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
        ("https://createto.ca/download/8", "text/csv"),
        ("https://createto.ca/download/9", "Text/Plain; charset=windows-1252"),
        ("https://createto.ca/download/10", "image/png"),
        ("https://createto.ca/download/11", "image/svg+xml"),
        # The extension already said it is a supported file: the header is not asked.
        (REPORT, "application/octet-stream"),
    ],
)
def test_a_supported_response_is_kept(url: str, content_type: str):
    assert response_refusal(url, response(content_type=content_type), MAX_FILE_BYTES) is None


@pytest.mark.parametrize(
    ("content_type", "media_type"),
    [
        ("application/zip", "application/zip"),
        ("application/x-msdownload", "application/x-msdownload"),
        ("video/mp4", "video/mp4"),
        ("application/json; charset=utf-8", "application/json"),
        ("application/octet-stream", "application/octet-stream"),
    ],
)
def test_an_unsupported_content_type_is_skipped_type(content_type: str, media_type: str):
    refused = response_refusal(
        "https://createto.ca/download", response(content_type=content_type), MAX_FILE_BYTES
    )
    assert refused == (FetchOutcome.SKIPPED_TYPE, f"content_type {media_type}")


def test_a_response_without_a_content_type_is_skipped_type():
    refused = response_refusal("https://createto.ca/download", response(), MAX_FILE_BYTES)
    assert refused == (FetchOutcome.SKIPPED_TYPE, "content_type application/octet-stream")


def test_a_content_length_over_100_mb_is_skipped_size():
    over = response(content_type="application/pdf", content_length=MAX_FILE_BYTES + 1)
    exactly = response(content_type="application/pdf", content_length=MAX_FILE_BYTES)

    assert response_refusal(REPORT, over, MAX_FILE_BYTES) == (
        FetchOutcome.SKIPPED_SIZE,
        f"content_length {MAX_FILE_BYTES + 1} > {MAX_FILE_BYTES}",
    )
    assert response_refusal(REPORT, exactly, MAX_FILE_BYTES) is None


class Chunks(httpx.AsyncByteStream):
    """`count` chunks of `size` bytes, counting how many were read."""

    def __init__(self, count: int, size: int) -> None:
        self.count, self.size, self.read = count, size, 0

    async def __aiter__(self):
        for _ in range(self.count):
            self.read += 1
            yield b"x" * self.size


def test_a_body_streaming_past_the_cap_is_dropped_without_reading_the_rest():
    stream = Chunks(100, 10)

    body = asyncio.run(read_body(httpx.Response(200, stream=stream), 25))

    assert body is None
    assert stream.read == 3


def test_a_body_within_the_cap_is_read_whole():
    body = asyncio.run(read_body(httpx.Response(200, stream=Chunks(3, 10)), 30))

    assert body == b"x" * 30
