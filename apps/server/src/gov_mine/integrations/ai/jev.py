"""Jev over OpenRouter's Decisions API (`POST /api/alpha/decisions`): a thin httpx client, since
the API is not chat completions. One choice question per request; the caller builds the body."""

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from gov_mine.integrations.ai import Usage

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
TIMEOUT = httpx.Timeout(60.0)


class JevError(Exception):
    """The provider failed or answered in a shape this client does not read."""


@dataclass(frozen=True, slots=True)
class Decision:
    """`probability` is `probabilities[choice]`; `answer` is the whole answer as Jev gave it,
    with every probability and its own confidence."""

    choice: str
    probability: float
    answer: dict[str, Any]
    usage: Usage


def encode_body(body: dict[str, Any]) -> bytes:
    """The request body exactly as sent, so its size can be kept under a budget."""
    return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()


def create_client(transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    """The client for model providers, one per process. Tests pass a mock transport."""
    return httpx.AsyncClient(timeout=TIMEOUT, transport=transport)


async def decide(
    http: httpx.AsyncClient, api_key: str, body: dict[str, Any], question: str
) -> Decision:
    """Ask `body`'s choice `question` and read its answer. Raises `JevError` on a transport
    error, a non-200, or an answer without a choice among the criteria."""
    try:
        response = await http.post(
            DECISIONS_URL,
            content=encode_body(body),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
    except httpx.HTTPError as exc:
        raise JevError(f"{type(exc).__name__}: {exc}") from exc
    if response.status_code != httpx.codes.OK:
        raise JevError(f"HTTP {response.status_code}: {response.text[:500]}")
    try:
        data = response.json()
        answer = data["answers"][question]
        choice = answer["choice"]
        probability = float(answer["probabilities"][choice])
        usage = data["usage"]
        cost = usage.get("cost")
        parsed_usage = Usage(
            input_tokens=int(usage["input_tokens"]),
            output_tokens=int(usage["output_tokens"]),
            reported_cost=None if cost is None else Decimal(str(cost)),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise JevError(f"Unreadable answer: {exc!r}: {response.text[:500]}") from exc
    if answer.get("type") != "choice" or choice not in body["questions"][question]["criteria"]:
        raise JevError(f"Unexpected answer: {answer}")
    return Decision(choice=choice, probability=probability, answer=answer, usage=parsed_usage)


__all__ = ["DECISIONS_URL", "Decision", "JevError", "create_client", "decide", "encode_body"]
