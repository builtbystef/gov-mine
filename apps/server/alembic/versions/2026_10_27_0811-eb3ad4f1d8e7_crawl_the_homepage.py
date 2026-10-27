"""The institutions, the web as fetched, and the runs that fetch it."""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "eb3ad4f1d8e7"
down_revision: str | Sequence[str] | None = "7bf101be8fbe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def checked(table: str, column: str, values: list[str]) -> sa.Column:
    """A checked string: text with a constraint listing the enum's values, as
    `db/checked_strings.py` declares it. Adding a value is a migration that drops
    `ck_<table>_<column>` and creates it with the new list."""
    listed = ", ".join(f"'{value}'" for value in values)
    constraint = sa.CheckConstraint(f"{column} IN ({listed})", name=op.f(f"ck_{table}_{column}"))
    return sa.Column(column, sa.Text(), constraint, nullable=False)


def upgrade() -> None:
    op.create_table(
        "domains",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=253), nullable=False),
        checked("domains", "crawl_policy", ["crawl", "files_only", "platform", "blocked"]),
        sa.Column("robots_txt", sa.Text(), nullable=True),
        sa.Column("robots_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("crawl_delay_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_domains")),
        sa.UniqueConstraint("name", name=op.f("uq_domains_name")),
    )
    op.create_table(
        "institutions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        checked(
            "institutions",
            "institution_type",
            [
                "state",
                "state_agency",
                "county",
                "city",
                "police_agency",
                "fire_department",
                "special_district",
                "k12_district",
                "higher_education",
                "municipal_agency",
            ],
        ),
        sa.Column("website_url", sa.String(length=2048), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("full_crawl_interval", sa.Interval(), nullable=False),
        sa.Column("paused", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_institutions")),
    )
    op.create_table(
        "crawl_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        checked("crawl_runs", "status", ["queued", "running", "finished", "failed", "cancelled"]),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            name=op.f("fk_crawl_runs_institution_id_institutions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_crawl_runs")),
    )
    op.create_index(
        op.f("ix_crawl_runs_institution_id"), "crawl_runs", ["institution_id"], unique=False
    )
    op.create_table(
        "webpages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("domain_id", sa.Uuid(), nullable=False),
        sa.Column("discovered_from_webpage_id", sa.Uuid(), nullable=True),
        sa.Column("etag", sa.String(length=1024), nullable=True),
        sa.Column("last_modified", sa.String(length=100), nullable=True),
        sa.Column("missing_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["discovered_from_webpage_id"],
            ["webpages.id"],
            name=op.f("fk_webpages_discovered_from_webpage_id_webpages"),
        ),
        sa.ForeignKeyConstraint(
            ["domain_id"], ["domains.id"], name=op.f("fk_webpages_domain_id_domains")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webpages")),
        sa.UniqueConstraint("url", name=op.f("uq_webpages_url")),
    )
    op.create_index(op.f("ix_webpages_domain_id"), "webpages", ["domain_id"], unique=False)
    op.create_table(
        "webpage_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("webpage_id", sa.Uuid(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=True),
        sa.Column("media_type", sa.String(length=255), nullable=False),
        sa.Column("parser", sa.String(length=64), nullable=True),
        checked(
            "webpage_snapshots", "text_status", ["parsing", "ready", "partial", "failed", "none"]
        ),
        sa.Column("text_error", sa.Text(), nullable=True),
        sa.Column("stated_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["webpage_id"], ["webpages.id"], name=op.f("fk_webpage_snapshots_webpage_id_webpages")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webpage_snapshots")),
        sa.UniqueConstraint(
            "webpage_id", "content_hash", name=op.f("uq_webpage_snapshots_webpage_id")
        ),
    )
    op.create_table(
        "fetches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("crawl_run_id", sa.Uuid(), nullable=False),
        sa.Column("webpage_id", sa.Uuid(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        checked(
            "fetches",
            "outcome",
            [
                "fetched",
                "not_modified",
                "unchanged",
                "blocked_robots",
                "skipped_scope",
                "skipped_type",
                "skipped_size",
                "skipped_depth",
                "failed_http",
                "failed_timeout",
            ],
        ),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["crawl_run_id"], ["crawl_runs.id"], name=op.f("fk_fetches_crawl_run_id_crawl_runs")
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["webpage_snapshots.id"],
            name=op.f("fk_fetches_snapshot_id_webpage_snapshots"),
        ),
        sa.ForeignKeyConstraint(
            ["webpage_id"], ["webpages.id"], name=op.f("fk_fetches_webpage_id_webpages")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fetches")),
    )
    op.create_index(
        "ix_fetches_crawl_run_id_outcome", "fetches", ["crawl_run_id", "outcome"], unique=False
    )
    op.create_index(op.f("ix_fetches_webpage_id"), "fetches", ["webpage_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_fetches_webpage_id"), table_name="fetches")
    op.drop_index("ix_fetches_crawl_run_id_outcome", table_name="fetches")
    op.drop_table("fetches")
    op.drop_table("webpage_snapshots")
    op.drop_index(op.f("ix_webpages_domain_id"), table_name="webpages")
    op.drop_table("webpages")
    op.drop_index(op.f("ix_crawl_runs_institution_id"), table_name="crawl_runs")
    op.drop_table("crawl_runs")
    op.drop_table("institutions")
    op.drop_table("domains")
