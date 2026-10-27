"""What each model costs, in USD per million tokens, as checked on the date that names the
list. A price change is a new version: rows keep the version they were priced with."""

from dataclasses import dataclass
from decimal import Decimal

PRICE_LIST_VERSION = "2026-10-27"


@dataclass(frozen=True, slots=True)
class Price:
    input_per_million: Decimal
    output_per_million: Decimal


PRICES: dict[str, Price] = {
    # Extraction and OCR.
    "openai/gpt-6-luna": Price(Decimal("0.10"), Decimal("0.50")),
    # Classification; its output is free.
    "typesafe/jev-1.14": Price(Decimal("0.042"), Decimal(0)),
}
