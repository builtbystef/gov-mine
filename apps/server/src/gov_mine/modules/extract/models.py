"""What we know: each run of an extractor over a snapshot (`extractions`), the records it found
(`records`), every state a record has been in (`record_snapshots`), and a citation per field
(`citations`). A record's current state is the `current_records` view."""

import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import DDL, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import column, table

from gov_mine.db.base import Base, CreatedAt, UUIDPrimaryKey
from gov_mine.db.checked_strings import checked_string


class RecordType(StrEnum):
    PROJECT = "project"
    NEWS_ITEM = "news_item"
    MEETING = "meeting"
    CONTACT = "contact"
    RFP = "rfp"
    GRANT = "grant"
    CONTRACT = "contract"


class FallbackReason(StrEnum):
    """Why the model ran: no rule matched the document, or the rule's output failed."""

    NO_RULE = "no_rule"
    VALIDATION_FAILED = "validation_failed"


class Extraction(UUIDPrimaryKey, CreatedAt, Base):
    """One run of one extractor (`model:<record_type>@<version>`) over one snapshot, never
    repeated. `raw_output` is the extractor's whole answer; `error` is set, with no records,
    when it failed. Its paid calls are `ai_calls` rows."""

    __tablename__ = "extractions"
    __table_args__ = (UniqueConstraint("snapshot_id", "extractor"),)

    # None for an extraction rerun by hand outside a run.
    crawl_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crawl_runs.id"), index=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webpage_snapshots.id"))
    record_type: Mapped[RecordType] = checked_string(RecordType, "record_type")
    extractor: Mapped[str] = mapped_column(String(64))
    fallback_reason: Mapped[FallbackReason | None] = checked_string(
        FallbackReason, "fallback_reason"
    )
    raw_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)


class Record(UUIDPrimaryKey, CreatedAt, Base):
    """One thing a document describes. `key` is the record type's key field's value, empty for
    types with one record per document."""

    __tablename__ = "records"
    __table_args__ = (UniqueConstraint("record_type", "document_id", "key"),)

    record_type: Mapped[RecordType] = checked_string(RecordType, "record_type")
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    key: Mapped[str] = mapped_column(Text)


class RecordSnapshot(UUIDPrimaryKey, CreatedAt, Base):
    """A state of a record, validated by its record type's model, written only when it differs
    from the previous one. `created_at` is when it was extracted."""

    __tablename__ = "record_snapshots"

    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("records.id"), index=True)
    extraction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("extractions.id"), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)


class Citation(UUIDPrimaryKey, CreatedAt, Base):
    """Where one field's value is: a page of the extraction's snapshot (from 1) and an excerpt.
    `verified` is set by the quote check, never by the extractor."""

    __tablename__ = "citations"

    record_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("record_snapshots.id"), index=True
    )
    field: Mapped[str] = mapped_column(String(64))
    page: Mapped[int] = mapped_column(Integer)
    excerpt: Mapped[str] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean)


# Each record's latest snapshot. The migration creates the same view.
CURRENT_RECORDS_SQL = """
CREATE OR REPLACE VIEW current_records AS
SELECT DISTINCT ON (r.id)
    r.id AS record_id, r.record_type, r.institution_id, r.document_id, r.key,
    s.id AS record_snapshot_id, s.extraction_id, s.data, s.created_at AS extracted_at
FROM records r
JOIN record_snapshots s ON s.record_id = r.id
ORDER BY r.id, s.created_at DESC, s.id DESC
"""
event.listen(Base.metadata, "after_create", DDL(CURRENT_RECORDS_SQL))
event.listen(Base.metadata, "before_drop", DDL("DROP VIEW IF EXISTS current_records"))

current_records = table(
    "current_records",
    column("record_id"),
    column("record_type"),
    column("institution_id"),
    column("document_id"),
    column("key"),
    column("record_snapshot_id"),
    column("extraction_id"),
    column("data"),
    column("extracted_at"),
)
