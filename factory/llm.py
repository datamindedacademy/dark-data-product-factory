"""Use an OpenRouter key (`LLM_API_KEY`, as in the other bootcamp courses) for every agent.

When `LLM_API_KEY` is set and no Anthropic credentials are, point the Anthropic clients at OpenRouter's
Anthropic-compatible endpoint (https://openrouter.ai/docs/guides/community/anthropic-agent-sdk.md).
Both the Claude Agent SDK and Agno's `Claude` model read these variables. An `ANTHROPIC_API_KEY` or a
`claude` login works as before.
"""

from __future__ import annotations

import os
import re

OPENROUTER = "https://openrouter.ai/api"


def configure() -> None:
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if key and not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("ANTHROPIC_AUTH_TOKEN"):
        os.environ.update(ANTHROPIC_BASE_URL=OPENROUTER, ANTHROPIC_AUTH_TOKEN=key, ANTHROPIC_API_KEY="")


def via_openrouter() -> bool:
    return os.getenv("ANTHROPIC_BASE_URL", "").rstrip("/") == OPENROUTER


def model_id(model: str) -> str:
    """claude-haiku-5-5 -> anthropic/claude-haiku-5.5 on OpenRouter; unchanged otherwise."""
    if not via_openrouter() or "/" in model:
        return model
    return "anthropic/" + re.sub(r"-(\d+)-(\d+)$", r"-\1.\2", model)


if __name__ == "__main__":
    os.environ["ANTHROPIC_BASE_URL"] = OPENROUTER
    assert model_id("claude-haiku-5-5") == "anthropic/claude-haiku-5.5"
    assert model_id("anthropic/claude-opus-5.5") == "anthropic/claude-opus-5.5"
    del os.environ["ANTHROPIC_BASE_URL"]
    assert model_id("claude-haiku-5-5") == "claude-haiku-5-5"
    print("ok")
