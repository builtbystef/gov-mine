"""The cost ledger: one row per paid call."""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from gov_mine.db.base import Base, CreatedAt, UUIDPrimaryKey
from gov_mine.db.checked_strings import checked_string


class AIPurpose(StrEnum):
    CLASSIFY = "classify"
    EXTRACT = "extract"
    OCR = "ocr"
    TRANSCRIBE = "transcribe"


class AICall(UUIDPrimaryKey, CreatedAt, Base):
    """`cost` is computed at insert from the price list named by `price_list_version`;
    `reported_cost` is what OpenRouter said it charged, kept to check the list against.
    A classify call sets `classification_id`, an extract call `extraction_id`."""

    __tablename__ = "ai_calls"
    __table_args__ = (Index("ix_ai_calls_crawl_run_id_purpose", "crawl_run_id", "purpose"),)

    # None only for an extraction rerun by hand outside a run.
    crawl_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crawl_runs.id"))
    classification_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("classifications.id"))
    extraction_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("extractions.id"))
    purpose: Mapped[AIPurpose] = checked_string(AIPurpose, "purpose")
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    # USD, with places for a single token of the cheapest model.
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 12))
    reported_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 12))
    price_list_version: Mapped[str] = mapped_column(String(20))
