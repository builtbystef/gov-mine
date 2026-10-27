from pathlib import Path

from gov_mine.integrations.parser import parse

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"


def test_the_createto_homepage_keeps_its_content_and_drops_the_chrome():
    parsed = parse((FIXTURES / "createto" / "homepage.html").read_bytes(), "text/html")

    assert parsed is not None
    assert parsed.parser == "html:compact@1"
    [markdown] = parsed.pages
    assert "# Building the city we love" in markdown
    assert "## News" in markdown
    assert "CreateTO applies a strategic city-wide lens" in markdown
    assert "* ![People walking near the Parkdale Hub]" in markdown
    assert "[Parkdale Hub](/projects/parkdale-hub)" in markdown
    # Navigation, header and footer, scripts, styles and SVG.
    assert "Skip to main content" not in markdown
    assert "Land Acknowledgement" not in markdown
    assert "Governance News and Board Meeting Materials" not in markdown
    assert "<script" not in markdown
    assert "<svg" not in markdown
    assert "function(" not in markdown


def test_a_table_is_kept():
    html = (
        b"<main><table><tr><th>Lot</th><th>Area</th></tr>"
        b"<tr><td>A</td><td>2 ha</td></tr></table></main>"
    )

    parsed = parse(html, "text/html")

    assert parsed is not None
    assert "| Lot | Area |" in parsed.pages[0]
    assert "| A | 2 ha |" in parsed.pages[0]
