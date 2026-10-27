"""When each host was last sent a request, which its next one waits its delay from.

Revision ID: ba61b2ed5666
Revises: eb3ad4f1d8e7
Create Date: 2026-10-27 09:10:02.916807
"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "ba61b2ed5666"
down_revision: str | Sequence[str] | None = "eb3ad4f1d8e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "domains", sa.Column("last_request_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("domains", "last_request_at")
