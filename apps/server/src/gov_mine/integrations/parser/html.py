"""HTML to markdown: compacted with selectolax, then converted with markdownify, the converter
MarkItDown uses, so pages and files read alike."""

from markdownify import ATX, markdownify
from selectolax.lexbor import LexborHTMLParser, LexborNode

HTML_PARSER = "html:compact@1"
HTML_MEDIA_TYPES = frozenset({"text/html", "application/xhtml+xml"})

# What carries no content: code, styling, drawings, and the controls of forms and embeds.
_NOISE = (
    'script, style, svg, noscript, template, iframe, form, button, link, meta, img[src^="data:"]'
)
# The site's chrome around the content.
_CHROME = "nav, footer, [role=navigation], [role=contentinfo], [role=banner], [role=search], aside"


def _inside_content(node: LexborNode) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.tag in {"main", "article"}:
            return True
        parent = parent.parent
    return False


def compact(html: str) -> str:
    """The HTML with scripts, styles, SVG, navigation, footers and the page header removed;
    a header inside `main` or `article` is the content's own and stays."""
    tree = LexborHTMLParser(html)
    for node in tree.css(f"{_NOISE}, {_CHROME}"):
        node.decompose()
    for node in tree.css("header"):
        if not _inside_content(node):
            node.decompose()
    body = tree.body
    return (body.html if body is not None else tree.html) or ""


def parse_html(data: bytes) -> str:
    html = data.decode("utf-8", errors="replace")
    markdown = markdownify(compact(html), heading_style=ATX)
    lines = [line.rstrip() for line in markdown.splitlines()]
    # Collapse the blank runs the removed elements leave behind.
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip() + "\n"
