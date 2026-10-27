import json
from decimal import Decimal
from typing import TYPE_CHECKING

import httpx2
import pytest
from pydantic import SecretStr
from pydantic_ai import Agent
from sqlalchemy import func, select

from gov_mine.integrations.ai import (
    PROVIDER,
    Usage,
    create_model,
    extract_model_settings,
    usages,
)
from gov_mine.modules.crawl.models import CrawlRun
from gov_mine.modules.institutions.models import Institution, InstitutionType
from gov_mine.modules.ledger import service as ledger
from gov_mine.modules.ledger.models import AICall, AIPurpose
from gov_mine.modules.ledger.prices import PRICE_LIST_VERSION

if TYPE_CHECKING:
    import uuid

    from tests.integration.conftest import Database

    from gov_mine.config import Settings

KEY = "sk-or-test-not-a-real-key"


async def _new_run(db: Database) -> uuid.UUID:
    async with db.session() as session:
        institution = Institution(
            name="CreateTO",
            institution_type=InstitutionType.MUNICIPAL_AGENCY,
            website_url="https://createto.ca/",
        )
        session.add(institution)
        await session.flush()
        run = CrawlRun(institution_id=institution.id, settings={"trigger": "cli"})
        session.add(run)
        await session.commit()
        return run.id


async def _record_two_calls(db: Database) -> list[AICall]:
    run_id = await _new_run(db)
    async with db.session() as session:
        extract = await ledger.record(
            session,
            run_id=run_id,
            purpose=AIPurpose.EXTRACT,
            provider=PROVIDER,
            model="openai/gpt-6-luna",
            usage=Usage(input_tokens=1_000_000, output_tokens=1_000_000),
        )
        classify = await ledger.record(
            session,
            run_id=run_id,
            purpose=AIPurpose.CLASSIFY,
            provider=PROVIDER,
            model="typesafe/jev-1.14",
            usage=Usage(input_tokens=1_000_000, output_tokens=12),
        )
        await session.commit()
        calls = {c.id: c for c in await session.scalars(select(AICall))}
        return [calls[extract], calls[classify]]


def test_record_prices_each_call_from_the_price_list(db: Database):
    extract, classify = db.run(_record_two_calls, db)

    assert extract.cost == Decimal("0.60")
    assert classify.cost == Decimal("0.042")
    for call in (extract, classify):
        assert call.price_list_version == PRICE_LIST_VERSION
        assert call.crawl_run_id is not None
        assert call.provider == "openrouter"
    assert (extract.purpose, extract.model) == (AIPurpose.EXTRACT, "openai/gpt-6-luna")
    assert (extract.input_tokens, extract.output_tokens) == (1_000_000, 1_000_000)
    assert classify.purpose is AIPurpose.CLASSIFY


async def _record_unpriced(db: Database) -> int:
    async with db.session() as session:
        with pytest.raises(ledger.UnpricedModelError):
            await ledger.record(
                session,
                run_id=None,
                purpose=AIPurpose.EXTRACT,
                provider=PROVIDER,
                model="openai/gpt-7",
                usage=Usage(input_tokens=10, output_tokens=10),
            )
        return await session.scalar(select(func.count()).select_from(AICall)) or 0


def test_a_model_not_in_the_price_list_raises_and_writes_nothing(db: Database):
    assert db.run(_record_unpriced, db) == 0


def _openrouter(request: httpx2.Request) -> httpx2.Response:
    """OpenRouter's chat completions endpoint, answering with usage and its cost."""
    assert request.headers["Authorization"] == f"Bearer {KEY}"
    body = json.loads(request.content)
    assert body["model"] == "openai/gpt-6-luna"
    assert body["reasoning"] == {"effort": "medium"}
    return httpx2.Response(
        200,
        json={
            "id": "gen-1",
            "object": "chat.completion",
            "created": 1_793_000_000,
            "model": "openai/gpt-6-luna",
            "provider": "OpenAI",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "CreateTO"},
                }
            ],
            "usage": {
                "prompt_tokens": 2000,
                "completion_tokens": 400,
                "total_tokens": 2400,
                "cost": 0.0004,
            },
        },
    )


async def _extract_over_openrouter(db: Database, settings: Settings) -> AICall:
    run_id = await _new_run(db)
    async with httpx2.AsyncClient(transport=httpx2.MockTransport(_openrouter)) as http:
        model = create_model(settings, settings.extract_model, http_client=http)
        assert model is not None
        result = await Agent(model).run(
            "Who owns this page?", model_settings=extract_model_settings(settings)
        )
    assert result.output == "CreateTO"
    async with db.session() as session:
        [usage] = usages(result.all_messages())
        call_id = await ledger.record(
            session,
            run_id=run_id,
            purpose=AIPurpose.EXTRACT,
            provider=PROVIDER,
            model=settings.extract_model,
            usage=usage,
        )
        await session.commit()
        call = await session.get(AICall, call_id)
        assert call is not None
        return call


def test_an_openrouter_call_is_recorded_with_its_reported_cost(db: Database, settings: Settings):
    keyed = settings.model_copy(update={"openrouter_api_key": SecretStr(KEY)})

    call = db.run(_extract_over_openrouter, db, keyed)

    assert (call.input_tokens, call.output_tokens) == (2000, 400)
    # 2000 * 0.10 / 1M + 400 * 0.50 / 1M
    assert call.cost == Decimal("0.0004")
    assert call.reported_cost == Decimal("0.0004")
    assert KEY not in repr(keyed)


def test_no_key_means_no_model(settings: Settings):
    assert settings.openrouter_api_key is None
    assert create_model(settings, settings.extract_model) is None
