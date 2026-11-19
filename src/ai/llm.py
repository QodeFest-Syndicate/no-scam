"""Thin wrapper around the Qwen gateway with a mandatory soft-fail path.

Every helper returns ``(value, error)``. A ``None`` value means "use the
deterministic rules instead" - the swarm must never fail a request because a
model call timed out.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from .config import LLMSettings, resolve_settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@lru_cache(maxsize=8)
def _client(model: str, base_url: str, api_key: str, timeout: float) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        max_retries=0,
        temperature=0,
    )


def settings_for(mode: str = "auto") -> LLMSettings | None:
    return resolve_settings(mode)


def is_enabled(mode: str = "auto") -> bool:
    return settings_for(mode) is not None


def structured_call(
    schema: type[SchemaT],
    *,
    system: str,
    human: str,
    mode: str = "auto",
) -> tuple[SchemaT | None, str | None]:
    """Ask the model for a structured object; degrade to ``(None, error)`` on any fault."""
    settings = settings_for(mode)
    if settings is None:
        return None, "llm_disabled"

    try:
        llm = _client(settings.model, settings.base_url, settings.api_key, settings.timeout)
        result: Any = llm.with_structured_output(schema).invoke(
            [("system", system), ("human", human)]
        )
        if isinstance(result, schema):
            return result, None
        return schema.model_validate(result), None
    except Exception as exc:  # network, auth, rate limit, schema drift
        return None, f"{type(exc).__name__}: {exc}"[:280]


def model_label(mode: str = "auto") -> str:
    settings = settings_for(mode)
    return f"llm:{settings.model}" if settings else "rules"
