from pathlib import Path

import pytest

from gov_mine.shared.robots import robots_allows, robots_crawl_delay, robots_url

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"
MERX = (FIXTURES / "merx" / "robots.txt").read_text()
CREATETO = (FIXTURES / "createto" / "robots.txt").read_text()


def test_robots_txt_is_at_the_root_of_the_urls_scheme_host_and_port():
    assert robots_url("https://createto.ca/projects/a?x=1#y") == "https://createto.ca/robots.txt"
    assert robots_url("http://docs.example:8080/a") == "http://docs.example:8080/robots.txt"


def test_the_saved_merx_robots_txt_asks_for_5_seconds():
    assert robots_crawl_delay(MERX, "my-bot") == 5.0


@pytest.mark.parametrize(
    ("path", "allowed"),
    [
        ("/public/solicitations/open", True),
        ("/public/solicitations/0000333884", True),
        ("/private/supplier/dashboard", False),
        ("/login", False),
        # Its wildcard rules.
        ("/public/solicitations/open?pageNumber=2&sort=date", False),
        ("/public/solicitations/open?keywords=createto", True),
    ],
)
def test_the_saved_merx_robots_txt_applies_its_star_group_to_my_bot(path: str, *, allowed: bool):
    assert robots_allows(MERX, f"https://www.merx.com{path}", "my-bot") is allowed


def test_the_saved_merx_robots_txt_blocks_named_ai_crawlers_but_not_my_bot():
    assert robots_allows(MERX, "https://www.merx.com/", "ClaudeBot") is False
    assert robots_allows(MERX, "https://www.merx.com/", "my-bot") is True


def test_the_saved_createto_robots_txt_allows_everything_and_asks_for_no_delay():
    assert robots_allows(CREATETO, "https://createto.ca/projects", "my-bot") is True
    assert robots_crawl_delay(CREATETO, "my-bot") is None


def test_a_url_disallowed_for_star_or_for_my_bot_is_not_allowed():
    robots = (
        "User-agent: *\nDisallow: /private/\nCrawl-delay: 2\n\n"
        "User-agent: my-bot\nDisallow: /drafts/\nCrawl-delay: 0.5\n\n"
        "User-agent: other-bot\nDisallow: /\n"
    )

    assert robots_allows(robots, "https://docs.example/private/a", "my-bot") is False
    assert robots_allows(robots, "https://docs.example/drafts/a", "my-bot") is False
    assert robots_allows(robots, "https://docs.example/guide", "my-bot") is True
    # The longer of the two groups' delays.
    assert robots_crawl_delay(robots, "my-bot") == 2.0


def test_an_empty_robots_txt_allows_every_path():
    assert robots_allows("", "https://docs.example/anything", "my-bot") is True
    assert robots_crawl_delay("", "my-bot") is None
