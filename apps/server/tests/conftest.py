"""The settings every test builds on. Nothing here touches the environment: the
configured server (environment or `.env`) is read once, and the tests get a copy
pointed at the test database."""

import os
from typing import TYPE_CHECKING

import pytest
from pydantic import PostgresDsn
from sqlalchemy.engine import make_url

from gov_mine.config import Settings

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import URL

# TEST_DATABASE_SUFFIX names the test databases apart, so test runs in two worktrees at once
# do not drop each other's.
TEST_DATABASE = "gov_mine_test" + os.environ.get("TEST_DATABASE_SUFFIX", "")

# The development server, as configured.
_configured = Settings()
_configured_url = make_url(str(_configured.database_url))
_test_url = _configured_url.set(database=TEST_DATABASE).render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def configured_url() -> URL:
    """The development server, for creating the test database."""
    return _configured_url


@pytest.fixture(scope="session")
def test_database_name() -> str:
    return TEST_DATABASE


@pytest.fixture
def settings() -> Settings:
    """The configured settings, on the test database. No OpenRouter key, whatever a
    local `.env` says: tests never call the model. A module or class that needs
    other values overrides this fixture, requesting it as the base."""
    return _configured.model_copy(
        update={
            "database_url": PostgresDsn(_test_url),
            "app_name": "Test API",
            "openrouter_api_key": None,
        }
    )


def _pdf_of(*pages: str) -> bytes:
    """A PDF with one line of Helvetica text per page."""
    count = len(pages)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids ["
        + b" ".join(b"%d 0 R" % (4 + 2 * i) for i in range(count))
        + b"] /Count %d >>" % count,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for i, text in enumerate(pages):
        stream = b"BT /F1 12 Tf 72 720 Td (%s) Tj ET" % text.encode()
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
            b" /Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % (5 + 2 * i)
        )
        objects.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


@pytest.fixture
def make_pdf() -> Callable[..., bytes]:
    """Builds a PDF with one line of text per page: `make_pdf("first", "second")`."""
    return _pdf_of
