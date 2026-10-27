from typing import TYPE_CHECKING

from pydantic_ai.messages import ModelResponse

from gov_mine.integrations.ai.models import ModelCall

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pydantic_ai.messages import ModelMessage
    from sqlalchemy.ext.asyncio import AsyncSession


def record_model_calls(
    session: AsyncSession, messages: Sequence[ModelMessage], *, source: str, request_id: str
) -> list[ModelCall]:
    """One `ModelCall` per model response in `messages`, added to the session.
    Not flushed: the caller commits with the rest of its turn."""
    calls = [
        ModelCall(
            source=source,
            model=message.model_name or "unknown",
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            cache_read_tokens=message.usage.cache_read_tokens,
            cache_write_tokens=message.usage.cache_write_tokens,
            request_id=request_id,
            created_at=message.timestamp,
        )
        for message in messages
        if isinstance(message, ModelResponse)
    ]
    session.add_all(calls)
    return calls
