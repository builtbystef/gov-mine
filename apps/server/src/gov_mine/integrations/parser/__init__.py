"""The parser port: a snapshot's bytes to markdown, one string per page. Pure and synchronous,
so callers run it off the event loop."""

from dataclasses import dataclass
from datetime import datetime

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
    """The pages of markdown in `data`, or None for a type kept without text."""
    if media_type in HTML_MEDIA_TYPES:
        return Parsed(pages=[parse_html(data)], parser=HTML_PARSER)
    return None


__all__ = ["ParseError", "Parsed", "parse"]
