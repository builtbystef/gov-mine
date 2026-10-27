"""Classifications, and the sources and documents they create.

Revision ID: 7dd3b3fe6a85
Revises: 5c2e8a1f0d47
Create Date: 2026-10-27 10:17:11.913441
"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "7dd3b3fe6a85"
down_revision: str | Sequence[str] | None = "5c2e8a1f0d47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DOCUMENT_TYPES = [
    "purchase_order",
    "meeting_minutes",
    "budget",
    "procurement_guidelines",
    "youtube",
    "rfp",
    "grants",
    "press_releases",
    "projects",
    "project_material",
    "annual_report",
    "strategic_plan",
    "staff_directory",
]


def checked(table: str, column: str, values: list[str]) -> sa.Column:
    """A checked string, as `db/checked_strings.py` declares it."""
    listed = ", ".join(f"'{value}'" for value in values)
    constraint = sa.CheckConstraint(f"{column} IN ({listed})", name=op.f(f"ck_{table}_{column}"))
    return sa.Column(column, sa.Text(), constraint, nullable=False)


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("webpage_id", sa.Uuid(), nullable=False),
        checked("sources", "document_type", DOCUMENT_TYPES),
        sa.Column("crawl_interval", sa.Interval(), nullable=False),
        sa.Column("next_crawl_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("extractor_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            name=op.f("fk_sources_institution_id_institutions"),
        ),
        sa.ForeignKeyConstraint(
            ["webpage_id"], ["webpages.id"], name=op.f("fk_sources_webpage_id_webpages")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
        sa.UniqueConstraint("webpage_id", "document_type", name=op.f("uq_sources_webpage_id")),
    )
    op.create_index(op.f("ix_sources_institution_id"), "sources", ["institution_id"], unique=False)
    op.create_table(
        "classifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("crawl_run_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("classifier", sa.String(length=64), nullable=False),
        sa.Column("choice", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("raw_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["crawl_run_id"],
            ["crawl_runs.id"],
            name=op.f("fk_classifications_crawl_run_id_crawl_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["webpage_snapshots.id"],
            name=op.f("fk_classifications_snapshot_id_webpage_snapshots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classifications")),
        sa.UniqueConstraint(
            "snapshot_id", "classifier", name=op.f("uq_classifications_snapshot_id")
        ),
    )
    op.create_index(
        op.f("ix_classifications_crawl_run_id"), "classifications", ["crawl_run_id"], unique=False
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("parent_document_id", sa.Uuid(), nullable=True),
        sa.Column("webpage_id", sa.Uuid(), nullable=False),
        checked("documents", "document_type", DOCUMENT_TYPES),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("document_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            name=op.f("fk_documents_institution_id_institutions"),
        ),
        sa.ForeignKeyConstraint(
            ["parent_document_id"],
            ["documents.id"],
            name=op.f("fk_documents_parent_document_id_documents"),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], name=op.f("fk_documents_source_id_sources")
        ),
        sa.ForeignKeyConstraint(
            ["webpage_id"], ["webpages.id"], name=op.f("fk_documents_webpage_id_webpages")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("webpage_id", name=op.f("uq_documents_webpage_id")),
    )
    op.create_index(
        op.f("ix_documents_institution_id"), "documents", ["institution_id"], unique=False
    )
    op.create_index(op.f("ix_documents_source_id"), "documents", ["source_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_ai_calls_classification_id_classifications"),
        "ai_calls",
        "classifications",
        ["classification_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_ai_calls_classification_id_classifications"), "ai_calls", type_="foreignkey"
    )
    op.drop_index(op.f("ix_documents_source_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_institution_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_classifications_crawl_run_id"), table_name="classifications")
    op.drop_table("classifications")
    op.drop_index(op.f("ix_sources_institution_id"), table_name="sources")
    op.drop_table("sources")
