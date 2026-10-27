"""The parser port: a snapshot's bytes to markdown, one string per page. Pure and synchronous,
so callers run it off the event loop."""

from dataclasses import dataclass
from datetime import datetime

from gov_mine.integrations.parser.files import (
    OFFICE,
    PDF,
    PDF_PARSER,
    TEXT_MEDIA_TYPES,
    TEXT_PARSER,
    parse_office,
    parse_pdf,
    parse_text,
)
from gov_mine.integrations.parser.html import HTML_MEDIA_TYPES, HTML_PARSER, parse_html


@dataclass(frozen=True, slots=True)
class Parsed:
    pages: list[str]
    # `<kind>:<name>@<version>`, stored on the snapshot.
    parser: str
    # The latest date the content states about itself; read from 017 on.
    stated_date: datetime | None = None


class ParseError(Exception):
    """The bytes could not be parsed; the message is stored as the snapshot's `text_error`."""


def parse(data: bytes, media_type: str) -> Parsed | None:
    """The pages of markdown in `data`, pages in order, or None for an image, which is kept
    without text. Raises `ParseError` when the bytes cannot be read or no parser takes the
    type."""
    if media_type.startswith("image/"):
        return None
    try:
        if media_type in HTML_MEDIA_TYPES:
            return Parsed(pages=[parse_html(data)], parser=HTML_PARSER)
        if media_type == PDF:
            return Parsed(pages=parse_pdf(data), parser=PDF_PARSER)
        if media_type in OFFICE:
            return Parsed(pages=parse_office(data, media_type), parser=OFFICE[media_type][0])
        if media_type in TEXT_MEDIA_TYPES:
            return Parsed(pages=parse_text(data), parser=TEXT_PARSER)
    # The libraries raise their own errors, any of which means these bytes do not parse.
    except Exception as exc:
        raise ParseError(f"{type(exc).__name__}: {exc}") from exc
    raise ParseError(f"No parser for {media_type}")


__all__ = ["ParseError", "Parsed", "parse"]
