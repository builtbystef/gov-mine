import pytest

from gov_mine.modules.extract.quote_check import excerpt_on_page

PAGE = """# Parkdale Hub

The **Parkdale Hub** will deliver up to 1,000 new homes at the corner of
[Queen Street West](https://example.com/queen) and Cowan Avenue.

| Phase | Date |
| --- | --- |
| Construction start | 2027 |

It is important to the community. Construction is expec-
ted to begin in spring 2027 with City part ners.
"""


@pytest.mark.parametrize(
    "excerpt",
    [
        "The Parkdale Hub will deliver up to 1,000 new homes",
        "the parkdale hub   WILL deliver",
        "at the corner of Queen Street West and Cowan Avenue.",
        "Construction start 2027",
        "with City partners",
    ],
)
def test_an_excerpt_on_the_page_is_verified(excerpt: str):
    assert excerpt_on_page(PAGE, excerpt)


@pytest.mark.parametrize(
    "excerpt",
    [
        "The Parkdale Hub will deliver 2,000 new homes",
        "Parkdale",
        "port to the community",
    ],
)
def test_an_excerpt_not_on_the_page_is_not_verified(excerpt: str):
    assert not excerpt_on_page(PAGE, excerpt)


def test_typographic_quotes_and_dashes_verify():
    page = "Phase 2 \u2013 the City\u2019s \u201cdesign\u201d review"
    assert excerpt_on_page(page, 'Phase 2 - the City\'s "design" review')
