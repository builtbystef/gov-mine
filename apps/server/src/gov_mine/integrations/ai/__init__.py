from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

if TYPE_CHECKING:
    from pydantic_ai.models import Model
    from pydantic_ai.settings import ModelSettings

    from gov_mine.config import Settings

AIProvider = Literal["openai"]
ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh", "max"]


@lru_cache(maxsize=4)
def _openai_model(api_key: str, model_name: str) -> Model:
    return OpenAIResponsesModel(model_name, provider=OpenAIProvider(api_key=api_key))


def create_model(settings: Settings) -> Model | None:
    """None when no key is configured: the caller decides what that means."""
    match settings.ai_provider:
        case "openai":
            if settings.openai_api_key is None:
                return None
            return _openai_model(settings.openai_api_key.get_secret_value(), settings.ai_model)


def model_settings(settings: Settings, *, cache_key: str) -> ModelSettings:
    """`cache_key` groups requests that share an instruction and tool prefix, so the
    provider can serve it from its cache."""
    match settings.ai_provider:
        case "openai":
            return OpenAIResponsesModelSettings(
                openai_reasoning_effort=settings.ai_reasoning_effort,
                openai_prompt_cache_key=cache_key,
            )


__all__ = ["AIProvider", "ReasoningEffort", "create_model", "model_settings"]
