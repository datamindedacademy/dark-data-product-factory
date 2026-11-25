"""LLM-as-judge for the graders that cannot be deterministic.

Used only when the benchmark runs with ``--judge``. The judge is a single-turn
Agno agent with no tools and a structured output, so it uses the same
credentials as the agents. Pick the model with FACTORY_JUDGE_MODEL.

Judges are themselves models with biases: calibrate them (run on golden and on
deliberately bad outputs) before trusting their scores - see docs/benchmark.md.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from factory import llm

JUDGE_MODEL = os.environ.get("FACTORY_JUDGE_MODEL") or "qwen/qwen4-max"


class Criterion(BaseModel):
    criterion: str
    score: int = Field(ge=1, le=5)
    rationale: str


class Verdict(BaseModel):
    criteria: list[Criterion]


SYSTEM = """You are a strict, consistent evaluator for a data team's benchmark.
Score each criterion from 1 (absent / wrong) to 5 (excellent, nothing to add) and
justify every score in one or two sentences, citing the artifact. Do not reward
length. If something is missing, the score for that criterion is at most 2."""


def _judge(task: str, artifact: str, criteria: list[str]) -> Verdict:
    from agno.agent import Agent

    prompt = (f"## Task given to the agent\n{task}\n\n## Artifact produced\n{artifact}\n\n"
              "## Criteria\n" + "\n".join(f"- {c}" for c in criteria))
    out = Agent(model=llm.model(JUDGE_MODEL), instructions=SYSTEM, output_schema=Verdict, telemetry=False).run(prompt)
    if not isinstance(out.content, Verdict):
        raise RuntimeError("judge returned no structured output")
    return out.content


def judge(task: str, artifact: str, criteria: list[str]) -> tuple[float, str]:
    """Return (score in 0..1, rationale text)."""
    items = _judge(task, artifact, criteria).criteria
    if not items:
        return 0.0, "judge returned no criteria"
    score = sum((c.score - 1) / 4 for c in items) / len(items)
    detail = "; ".join(f"{c.criterion[:40]}={c.score}: {c.rationale}" for c in items)
    return score, detail
