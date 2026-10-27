"""One spelling for text that a page and a quote of it write differently: markdown syntax
stripped, case folded, whitespace collapsed, typographic punctuation evened out, mojibake
repaired. Shared by `text_hash` and the quote check. Copied from Public Atlas's
`shared/text.py`, with the markdown stripping added."""

import hashlib
import re
import unicodedata

# Typographic punctuation a page and a quote of it spell differently.
_PUNCTUATION = str.maketrans(
    {
        0x2018: "'",  # left single quotation mark
        0x2019: "'",  # right single quotation mark, the apostrophe pages write
        0x201A: "'",
        0x201B: "'",
        0x201C: '"',
        0x201D: '"',
        0x201E: '"',
        0x2013: "-",  # en dash
        0x2014: "-",  # em dash
        0x2212: "-",  # minus sign
        0x00A0: " ",  # no-break space
    }
)
# UTF-8 bytes read as Windows-1252 or Latin-1: a lead byte (U+00C2 to U+00F4) and one to three
# continuation bytes, as either encoding shows them.
_CONTINUATION = (
    r"\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc"
    r"\u2013\u2014\u2018-\u201e\u2020-\u2022\u2026\u2030\u2039\u203a\u20ac\u2122"
)
_MOJIBAKE = re.compile(rf"[\u00c2-\u00f4][{_CONTINUATION}]{{1,3}}")

# Markdown syntax, as markdownify and MarkItDown write it.
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~])")
_RULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$", re.MULTILINE)
_TABLE_DIVIDER = re.compile(r"^[\s|:-]*-[\s|:-]*$", re.MULTILINE)
_LINE_MARK = re.compile(r"^[ \t]*(?:#{1,6}[ \t]+|>[ \t]?|[-*+][ \t]+|\d+[.)][ \t]+)", re.MULTILINE)
_EMPHASIS = re.compile(r"\*\*|__|~~|`|(?<!\w)[*_]|[*_](?!\w)")


def repair_mojibake(text: str) -> str:
    """UTF-8 read as Windows-1252 or Latin-1 put right: "CafÃ©" means "Café". A run that does
    not decode cleanly is left as it is."""

    def fix(match: re.Match[str]) -> str:
        run = match.group()
        try:
            return b"".join(_single_byte(char) for char in run).decode("utf-8")
        except UnicodeError:
            return run

    return _MOJIBAKE.sub(fix, text)


def _single_byte(char: str) -> bytes:
    try:
        return char.encode("cp1252")
    except UnicodeEncodeError:
        return char.encode("latin-1")


def strip_markdown(text: str) -> str:
    """The words of a markdown text without its syntax: link and image text kept, their
    targets, emphasis, headings, list and quote marks, table pipes and rules dropped."""
    text = _IMAGE.sub(r"\1", text)
    text = _LINK.sub(r"\1", text)
    text = _RULE.sub(" ", text)
    text = _TABLE_DIVIDER.sub(" ", text)
    text = _LINE_MARK.sub("", text)
    text = text.replace("|", " ")
    text = _EMPHASIS.sub("", text)
    return _ESCAPE.sub(r"\1", text)


def normalize_text(text: str) -> str:
    """Case folded, whitespace collapsed, typographic punctuation evened out, mojibake
    repaired: the form two texts are compared in."""
    text = repair_mojibake(text).translate(_PUNCTUATION)
    return " ".join(unicodedata.normalize("NFKC", text).split()).casefold()


def normalize_markdown(text: str) -> str:
    """`normalize_text` of the markdown's words."""
    return normalize_text(strip_markdown(text))


def text_hash(pages: list[str]) -> str:
    """SHA-256 of a text's normalised markdown, pages in order: equal when only markdown
    syntax, case or spacing changed."""
    return hashlib.sha256(
        "\n".join(normalize_markdown(page) for page in pages).encode()
    ).hexdigest()


__all__ = ["normalize_markdown", "normalize_text", "repair_mojibake", "strip_markdown", "text_hash"]
