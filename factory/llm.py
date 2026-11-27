"""The model behind every agent: OpenRouter, with the key in `LLM_API_KEY`, as in the other bootcamp courses.

Every agent runs on one model, the same for every team, so the score measures the agents and not the model.
OpenRouter reports the cost of every call.
"""

from __future__ import annotations

import os

MODEL = "google/gemma-4-31b-it"  # small, open and cheap on purpose: the baseline leaves room


def model(effort: str | None = None):
    """The Agno model. `effort` (low | medium | high) makes it reason before it answers."""
    from agno.models.openrouter import OpenRouter

    key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("set LLM_API_KEY to an OpenRouter API key")
    # max_tokens: provider defaults are small, and a reasoning model that runs out mid-answer just stops
    return OpenRouter(id=MODEL, api_key=key, reasoning_effort=effort, max_tokens=16_000,
                      extra_body={"usage": {"include": True}})
