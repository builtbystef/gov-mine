"""Models over OpenRouter, with one key for all of them. Extraction and OCR go through Pydantic
AI (`create_model`); Jev's Decisions API is called directly and reads its `usage` into a
`Usage` the same way. The ledger prices a `Usage`; this package never writes rows."""

from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider

if TYPE_CHECKING:
    from collections.abc import Sequence

    import httpx2
    from pydantic_ai.messages import ModelMessage
    from pydantic_ai.models import Model

    from gov_mine.config import Settings

# The `provider` an `ai_calls` row names.
PROVIDER = "openrouter"

# OpenRouter's reasoning effort levels.
ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]


@dataclass(frozen=True, slots=True)
class Usage:
    """What one paid call used. `reported_cost` is the USD OpenRouter charged, when it says;
    the ledger's own cost comes from the price list."""

    input_tokens: int
    output_tokens: int
    reported_cost: Decimal | None = None


def _provider(api_key: str, http_client: httpx2.AsyncClient | None = None) -> OpenRouterProvider:
    """The OpenAI client's own retries are off: callers decide how often to try again."""
    built = OpenRouterProvider(api_key=api_key, http_client=http_client)
    return OpenRouterProvider(openai_client=built.client.with_options(max_retries=0))


@lru_cache(maxsize=4)
def _model(api_key: str, model_name: str) -> Model:
    return OpenRouterModel(model_name, provider=_provider(api_key))


def create_model(
    settings: Settings, model_name: str, *, http_client: httpx2.AsyncClient | None = None
) -> Model | None:
    """None when no key is configured: nothing calls a model then. `http_client` is for tests,
    which answer OpenRouter's requests themselves."""
    if settings.openrouter_api_key is None:
        return None
    api_key = settings.openrouter_api_key.get_secret_value()
    if http_client is None:
        return _model(api_key, model_name)
    return OpenRouterModel(model_name, provider=_provider(api_key, http_client))


def extract_model_settings(settings: Settings) -> OpenRouterModelSettings:
    """For the extraction (and OCR) model. `usage.include` asks OpenRouter for each call's
    cost."""
    return OpenRouterModelSettings(
        openrouter_reasoning={"effort": settings.extract_reasoning_effort},
        openrouter_usage={"include": True},
    )


def usage_of(response: ModelResponse) -> Usage:
    cost = (response.provider_details or {}).get("cost")
    return Usage(
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        reported_cost=None if cost is None else Decimal(str(cost)),
    )


def usages(messages: Sequence[ModelMessage]) -> list[Usage]:
    """One `Usage` per model response in an agent run's messages: each was a paid call."""
    return [usage_of(message) for message in messages if isinstance(message, ModelResponse)]


__all__ = [
    "PROVIDER",
    "ReasoningEffort",
    "Usage",
    "create_model",
    "extract_model_settings",
    "usage_of",
    "usages",
]
