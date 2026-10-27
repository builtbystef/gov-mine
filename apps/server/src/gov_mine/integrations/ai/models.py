from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from gov_mine.db.base import Base, UUIDPrimaryKey


class ModelCall(UUIDPrimaryKey, Base):
    """One request to a model: from which feature, and what it cost in tokens.
    The app's own record, for reporting; Logfire sees the same numbers, for
    debugging.

    `source` names the feature, and `request_id` ties the row to that request's
    log lines."""

    __tablename__ = "model_calls"

    source: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    cache_read_tokens: Mapped[int]
    cache_write_tokens: Mapped[int]
    request_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
