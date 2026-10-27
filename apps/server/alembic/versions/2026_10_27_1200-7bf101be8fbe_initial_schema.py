from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from procrastinate.schema import SchemaManager

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "7bf101be8fbe"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# What Procrastinate 3.9's schema creates, for `downgrade`. On a Procrastinate
# upgrade, add a migration that runs the new files from
# `procrastinate/sql/migrations/` (`procrastinate schema --migrations-path`).
PROCRASTINATE_TABLES = [
    "procrastinate_workers",
    "procrastinate_jobs",
    "procrastinate_periodic_defers",
    "procrastinate_events",
]
PROCRASTINATE_TYPES = [
    "procrastinate_job_status",
    "procrastinate_job_event_type",
    "procrastinate_job_to_defer_v1",
]
PROCRASTINATE_FUNCTIONS = [
    "procrastinate_defer_jobs_v1",
    "procrastinate_defer_periodic_job_v2",
    "procrastinate_fetch_job_v2",
    "procrastinate_finish_job_v1",
    "procrastinate_cancel_job_v1",
    "procrastinate_retry_job_v1",
    "procrastinate_retry_job_v2",
    "procrastinate_notify_queue_job_inserted_v1",
    "procrastinate_notify_queue_abort_job_v1",
    "procrastinate_trigger_function_status_events_insert_v1",
    "procrastinate_trigger_function_status_events_update_v1",
    "procrastinate_trigger_function_scheduled_events_v1",
    "procrastinate_trigger_abort_requested_events_procedure_v1",
    "procrastinate_unlink_periodic_defers_v1",
    "procrastinate_register_worker_v1",
    "procrastinate_unregister_worker_v1",
    "procrastinate_update_heartbeat_v1",
    "procrastinate_prune_stalled_workers_v1",
]


def upgrade() -> None:
    # --- App tables --------------------------------------------------------------
    # model_calls belongs to integrations/ai.
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

    # --- Job queue (Procrastinate) -----------------------------------------------
    # Straight to the driver, which reads `%` as a placeholder even with no
    # parameters, so the schema's own are doubled.
    op.get_bind().exec_driver_sql(SchemaManager.get_schema().replace("%", "%%"))


def downgrade() -> None:
    # --- Job queue (Procrastinate) -----------------------------------------------
    # Functions first, with the triggers on them: some return a table's row
    # type and would go with the table.
    for function in PROCRASTINATE_FUNCTIONS:
        op.execute(f"DROP FUNCTION {function} CASCADE")
    for table in PROCRASTINATE_TABLES:
        op.execute(f"DROP TABLE {table} CASCADE")
    for type_ in PROCRASTINATE_TYPES:
        op.execute(f"DROP TYPE {type_}")

    # --- App tables --------------------------------------------------------------
    op.drop_table("model_calls")
