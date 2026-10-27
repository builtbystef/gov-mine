import asyncio
import socket
from ipaddress import ip_address
from urllib.parse import urlsplit

import pytest

from gov_mine.modules.crawl import service
from gov_mine.modules.crawl.models import CrawlPolicy, FetchOutcome
from gov_mine.modules.crawl.service import address_refusal, refusal
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
