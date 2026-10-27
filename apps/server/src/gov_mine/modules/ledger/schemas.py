import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from gov_mine.modules.ledger.models import AIPurpose


class AICallOutput(BaseModel):
    """One paid call. `cost` is from the price list; `reported_cost` is what OpenRouter said."""

    id: uuid.UUID
    crawl_run_id: uuid.UUID | None
    classification_id: uuid.UUID | None
    extraction_id: uuid.UUID | None
    purpose: AIPurpose
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: Decimal
    reported_cost: Decimal | None
    price_list_version: str
    created_at: datetime
