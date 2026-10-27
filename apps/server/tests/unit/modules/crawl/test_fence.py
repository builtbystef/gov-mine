import pytest

from gov_mine.modules.crawl.models import CrawlPolicy, FetchOutcome
from gov_mine.modules.crawl.service import refusal

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
