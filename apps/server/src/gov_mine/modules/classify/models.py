"""What each page is (`classifications`), and what the institution published: listing pages
worth revisiting (`sources`) and pages or files worth keeping (`documents`)."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Interval, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from gov_mine.db.base import Base, CreatedAt, UUIDPrimaryKey
from gov_mine.db.checked_strings import checked_string
from gov_mine.modules.institutions.models import DocumentType


class Classification(UUIDPrimaryKey, CreatedAt, Base):
    """One run of the classifier over a webpage's first snapshot with text. `choice` is `none`,
    `listing:<type>` or `document:<type>`, null with `error` when the provider failed;
    `confidence` is the choice's probability; `raw_output` is the classifier's whole answer."""

    __tablename__ = "classifications"
    __table_args__ = (UniqueConstraint("snapshot_id", "classifier"),)

    crawl_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crawl_runs.id"), index=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webpage_snapshots.id"))
    classifier: Mapped[str] = mapped_column(String(64))
    choice: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float | None] = mapped_column(Float)
    raw_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)


class Source(UUIDPrimaryKey, CreatedAt, Base):
    """A page that lists documents of one type, revisited every `crawl_interval`."""

    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("webpage_id", "document_type"),)

    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    webpage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webpages.id"))
    document_type: Mapped[DocumentType] = checked_string(DocumentType, "document_type")
    crawl_interval: Mapped[timedelta] = mapped_column(Interval)
    next_crawl_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # The rule extractor, copied from a named rule in code (`sources set-rule`).
    extractor_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class Document(UUIDPrimaryKey, CreatedAt, Base):
    """A page or file worth keeping. `source_id` is the listing it was found under, if any;
    `document_date` is the date the five-year window reads, null meaning current."""

    __tablename__ = "documents"

    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id"), index=True)
    parent_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id"))
    webpage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webpages.id"), unique=True)
    document_type: Mapped[DocumentType] = checked_string(DocumentType, "document_type")
    title: Mapped[str | None] = mapped_column(Text)
    document_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
