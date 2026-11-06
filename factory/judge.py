"""LLM-as-judge for the graders that cannot be deterministic.

Used only when the benchmark runs with ``--judge``. The judge is a single-turn
Agent SDK call with no tools and a JSON-schema output, so it uses the same
credentials as the agents. Pick the model with FACTORY_JUDGE_MODEL.

Judges are themselves models with biases: calibrate them (run on golden and on
deliberately bad outputs) before trusting their scores - see docs/benchmark.md.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

JUDGE_MODEL = os.environ.get("FACTORY_JUDGE_MODEL") or "claude-sonnet-5-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "score": {"type": "integer", "minimum": 1, "maximum": 5},
                    "rationale": {"type": "string"},
                },
                "required": ["criterion", "score", "rationale"],
            },
        },
    },
    "required": ["criteria"],
}

SYSTEM = """You are a strict, consistent evaluator for a data team's benchmark.
Score each criterion from 1 (absent / wrong) to 5 (excellent, nothing to add) and
justify every score in one or two sentences, citing the artifact. Do not reward
length. If something is missing, the score for that criterion is at most 2."""


async def _judge(task: str, artifact: str, criteria: list[str]) -> dict[str, Any]:
    prompt = (f"## Task given to the agent\n{task}\n\n## Artifact produced\n{artifact}\n\n"
              "## Criteria\n" + "\n".join(f"- {c}" for c in criteria))
    opts = ClaudeAgentOptions(model=JUDGE_MODEL, system_prompt=SYSTEM, tools=[], max_turns=2,
                              setting_sources=[], output_format={"type": "json_schema", "schema": SCHEMA})
    result: Any = None
    async for msg in query(prompt=prompt, options=opts):
        if isinstance(msg, ResultMessage):
            result = msg.structured_output or (json.loads(msg.result) if msg.result else None)
    if not result:
        raise RuntimeError("judge returned no structured output")
    return result


def judge(task: str, artifact: str, criteria: list[str]) -> tuple[float, str]:
    """Return (score in 0..1, rationale text)."""
    res = asyncio.run(_judge(task, artifact, criteria))
    items = res.get("criteria", [])
    if not items:
        return 0.0, "judge returned no criteria"
    score = sum((c["score"] - 1) / 4 for c in items) / len(items)
    detail = "; ".join(f"{c['criterion'][:40]}={c['score']}: {c['rationale']}" for c in items)
    return score, detail
