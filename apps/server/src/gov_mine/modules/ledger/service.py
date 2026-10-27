from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from gov_mine.modules.ledger.models import AICall, AIPurpose
from gov_mine.modules.ledger.prices import PRICE_LIST_VERSION, PRICES, Price
from gov_mine.shared.exceptions import AppError

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from gov_mine.integrations.ai import Usage

MILLION = Decimal(1_000_000)


class UnpricedModelError(AppError):
    """A model the price list does not know: no call to it may be made."""


def price_of(model: str) -> Price:
    """Callers check this before calling a model, so no call is ever unpriced."""
    try:
        return PRICES[model]
    except KeyError:
        raise UnpricedModelError(
            f"{model} is not in price list {PRICE_LIST_VERSION} (modules/ledger/prices.py)"
        ) from None


def cost_of(model: str, usage: Usage) -> Decimal:
    price = price_of(model)
    spent = (
        usage.input_tokens * price.input_per_million
        + usage.output_tokens * price.output_per_million
    )
    return spent / MILLION


async def record(  # noqa: PLR0913 - the spec's ledger.record, keyword-only
    session: AsyncSession,
    *,
    run_id: uuid.UUID | None,
    purpose: AIPurpose,
    provider: str,
    model: str,
    usage: Usage,
    classification_id: uuid.UUID | None = None,
    extraction_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """One `ai_calls` row for one paid call, flushed for its id; the caller commits."""
    call = AICall(
        crawl_run_id=run_id,
        classification_id=classification_id,
        extraction_id=extraction_id,
        purpose=purpose,
        provider=provider,
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cost=cost_of(model, usage),
        reported_cost=usage.reported_cost,
        price_list_version=PRICE_LIST_VERSION,
    )
    session.add(call)
    await session.flush()
    return call.id


async def list_calls(
    session: AsyncSession, run_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[AICall], int]:
    """The run's calls by purpose, oldest first within each."""
    where = AICall.crawl_run_id == run_id
    total = await session.scalar(select(func.count()).select_from(AICall).where(where)) or 0
    calls = await session.scalars(
        select(AICall)
        .where(where)
        .order_by(AICall.purpose, AICall.created_at, AICall.id)
        .limit(limit)
        .offset(offset)
    )
    return list(calls), total
