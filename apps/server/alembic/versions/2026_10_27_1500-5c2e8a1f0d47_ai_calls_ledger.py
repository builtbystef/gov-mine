"""The cost ledger `ai_calls` replaces `model_calls`.

Revision ID: 5c2e8a1f0d47
Revises: ba61b2ed5666
Create Date: 2026-10-27 15:00:00.000000
"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "5c2e8a1f0d47"
down_revision: str | Sequence[str] | None = "ba61b2ed5666"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PURPOSES = ["classify", "extract", "ocr", "transcribe"]


def upgrade() -> None:
    op.drop_table("model_calls")
    listed = ", ".join(f"'{value}'" for value in PURPOSES)
    op.create_table(
        "ai_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("crawl_run_id", sa.Uuid(), nullable=True),
        sa.Column("classification_id", sa.Uuid(), nullable=True),
        sa.Column("extraction_id", sa.Uuid(), nullable=True),
        sa.Column(
            "purpose",
            sa.Text(),
            sa.CheckConstraint(f"purpose IN ({listed})", name=op.f("ck_ai_calls_purpose")),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Numeric(precision=18, scale=12), nullable=False),
        sa.Column("reported_cost", sa.Numeric(precision=18, scale=12), nullable=True),
        sa.Column("price_list_version", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["crawl_run_id"], ["crawl_runs.id"], name=op.f("fk_ai_calls_crawl_run_id_crawl_runs")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_calls")),
    )
    op.create_index(
        "ix_ai_calls_crawl_run_id_purpose", "ai_calls", ["crawl_run_id", "purpose"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_ai_calls_crawl_run_id_purpose", table_name="ai_calls")
    op.drop_table("ai_calls")
    op.create_table(
        "model_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_write_tokens", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_calls")),
    )
