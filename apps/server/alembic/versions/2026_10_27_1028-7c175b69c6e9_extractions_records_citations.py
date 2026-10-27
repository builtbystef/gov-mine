"""Extractions, records, record snapshots and citations; the current_records view; pg_trgm.

Revision ID: 7c175b69c6e9
Revises: 7dd3b3fe6a85
Create Date: 2026-10-27 10:28:12.388099
"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "7c175b69c6e9"
down_revision: str | Sequence[str] | None = "7dd3b3fe6a85"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RECORD_TYPES = ["project", "news_item", "meeting", "contact", "rfp", "grant", "contract"]
FALLBACK_REASONS = ["no_rule", "validation_failed"]

CURRENT_RECORDS = """
CREATE OR REPLACE VIEW current_records AS
SELECT DISTINCT ON (r.id)
    r.id AS record_id, r.record_type, r.institution_id, r.document_id, r.key,
    s.id AS record_snapshot_id, s.extraction_id, s.data, s.created_at AS extracted_at
FROM records r
JOIN record_snapshots s ON s.record_id = r.id
ORDER BY r.id, s.created_at DESC, s.id DESC
"""


def checked(table: str, column: str, values: list[str], *, nullable: bool = False) -> sa.Column:
    """A checked string, as `db/checked_strings.py` declares it."""
    listed = ", ".join(f"'{value}'" for value in values)
    constraint = sa.CheckConstraint(f"{column} IN ({listed})", name=op.f(f"ck_{table}_{column}"))
    return sa.Column(column, sa.Text(), constraint, nullable=nullable)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "extractions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("crawl_run_id", sa.Uuid(), nullable=True),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        checked("extractions", "record_type", RECORD_TYPES),
        sa.Column("extractor", sa.String(length=64), nullable=False),
        checked("extractions", "fallback_reason", FALLBACK_REASONS, nullable=True),
        sa.Column("raw_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["crawl_run_id"], ["crawl_runs.id"], name=op.f("fk_extractions_crawl_run_id_crawl_runs")
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["webpage_snapshots.id"],
            name=op.f("fk_extractions_snapshot_id_webpage_snapshots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extractions")),
        sa.UniqueConstraint("snapshot_id", "extractor", name=op.f("uq_extractions_snapshot_id")),
    )
    op.create_index(
        op.f("ix_extractions_crawl_run_id"), "extractions", ["crawl_run_id"], unique=False
    )
    op.create_table(
        "records",
        sa.Column("id", sa.Uuid(), nullable=False),
        checked("records", "record_type", RECORD_TYPES),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], name=op.f("fk_records_document_id_documents")
        ),
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            name=op.f("fk_records_institution_id_institutions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_records")),
        sa.UniqueConstraint(
            "record_type", "document_id", "key", name=op.f("uq_records_record_type")
        ),
    )
    op.create_index(op.f("ix_records_document_id"), "records", ["document_id"], unique=False)
    op.create_index(op.f("ix_records_institution_id"), "records", ["institution_id"], unique=False)
    op.create_table(
        "record_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("extraction_id", sa.Uuid(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["extraction_id"],
            ["extractions.id"],
            name=op.f("fk_record_snapshots_extraction_id_extractions"),
        ),
        sa.ForeignKeyConstraint(
            ["record_id"], ["records.id"], name=op.f("fk_record_snapshots_record_id_records")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_record_snapshots")),
    )
    op.create_index(
        op.f("ix_record_snapshots_extraction_id"),
        "record_snapshots",
        ["extraction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_record_snapshots_record_id"), "record_snapshots", ["record_id"], unique=False
    )
    op.create_table(
        "citations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("record_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("field", sa.String(length=64), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["record_snapshot_id"],
            ["record_snapshots.id"],
            name=op.f("fk_citations_record_snapshot_id_record_snapshots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_citations")),
    )
    op.create_index(
        op.f("ix_citations_record_snapshot_id"), "citations", ["record_snapshot_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_ai_calls_extraction_id_extractions"),
        "ai_calls",
        "extractions",
        ["extraction_id"],
        ["id"],
    )
    op.execute(CURRENT_RECORDS)


def downgrade() -> None:
    op.execute("DROP VIEW current_records")
    op.drop_constraint(
        op.f("fk_ai_calls_extraction_id_extractions"), "ai_calls", type_="foreignkey"
    )
    op.drop_index(op.f("ix_citations_record_snapshot_id"), table_name="citations")
    op.drop_table("citations")
    op.drop_index(op.f("ix_record_snapshots_record_id"), table_name="record_snapshots")
    op.drop_index(op.f("ix_record_snapshots_extraction_id"), table_name="record_snapshots")
    op.drop_table("record_snapshots")
    op.drop_index(op.f("ix_records_institution_id"), table_name="records")
    op.drop_index(op.f("ix_records_document_id"), table_name="records")
    op.drop_table("records")
    op.drop_index(op.f("ix_extractions_crawl_run_id"), table_name="extractions")
    op.drop_table("extractions")
