import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from gov_mine.db.base import Base, CreatedAt, UUIDPrimaryKey
from gov_mine.db.checked_strings import checked_string


class TextStatus(StrEnum):
    PARSING = "parsing"
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"
    NONE = "none"


class WebpageSnapshot(UUIDPrimaryKey, CreatedAt, Base):
    """A stored copy of a webpage: the bytes at `bytes/<id>` in object storage, written only when
    `content_hash` is new for the webpage. `size_bytes` is the stored length."""

    __tablename__ = "webpage_snapshots"
    __table_args__ = (UniqueConstraint("webpage_id", "content_hash"),)

    webpage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webpages.id"))
    # SHA-256 of the bytes, hex.
    content_hash: Mapped[str] = mapped_column(String(64))
    text_hash: Mapped[str | None] = mapped_column(String(64))
    media_type: Mapped[str] = mapped_column(String(255))
    # Which parser produced the text, as `<kind>:<name>@<version>`.
    parser: Mapped[str | None] = mapped_column(String(64))
    text_status: Mapped[TextStatus] = checked_string(
        TextStatus, "text_status", default=TextStatus.PARSING
    )
    text_error: Mapped[str | None] = mapped_column(Text)
    stated_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
