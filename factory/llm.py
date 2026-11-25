"""The model behind every agent: OpenRouter, with the key in `LLM_API_KEY`, as in the other bootcamp courses.

Model ids are OpenRouter's (https://openrouter.ai/models), e.g. `google/gemma-4-31b-it` or `google/gemma-4-31b-it`.
OpenRouter reports the cost of every call, so every model is priced the same way.
"""

from __future__ import annotations

import os

DEFAULT_MODEL = os.environ.get("FACTORY_MODEL") or "google/gemma-4-31b-it"  # small, open and cheap on purpose: the baseline leaves room


def model(model_id: str, effort: str | None = None):
    """An Agno model for one OpenRouter model id. `effort` (low | medium | high) only matters for reasoning models."""
    from agno.models.openrouter import OpenRouter

    key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("set LLM_API_KEY to an OpenRouter API key")
    # max_tokens: provider defaults are small, and a reasoning model that runs out mid-answer just stops
    return OpenRouter(id=model_id, api_key=key, reasoning_effort=effort, max_tokens=16_000,
                      extra_body={"usage": {"include": True}})
