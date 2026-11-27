"""answers.json: one entry per question of the request, a number or a flat map of numbers.

The issue shows the expected shape in a ```json block under "## Answers". The line uses that
template to check the shape; the graders compare the values with the right answers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

TOLERANCE = 0.005  # relative: within 0.5% of the right answer counts as right


def template(issue: str) -> dict[str, Any]:
    """The answers.json template in the issue, or {} when there is none."""
    m = re.search(r"##\s*Answers.*?```json\s*(\{.*?\})\s*```", issue, re.DOTALL | re.IGNORECASE)
    return json.loads(m.group(1)) if m else {}


def shape_problems(answers: Any, tpl: dict[str, Any]) -> list[str]:
    """What is missing or of the wrong type, compared with the template. Values are not checked."""
    if not isinstance(answers, dict):
        return ["answers.json is not a JSON object"]
    problems = []
    for q, t in tpl.items():
        a = answers.get(q)
        if a is None:
            problems.append(f"{q} is missing")
        elif isinstance(t, dict):
            if not isinstance(a, dict):
                problems.append(f"{q} must be an object with the keys {sorted(t)}")
            else:
                problems += [f"{q}: key {k!r} is missing" for k in t if k not in a]
                problems += [f"{q}: {k!r} is not a number" for k in t if k in a and not _number(a[k])]
        elif not _number(a):
            problems.append(f"{q} must be a number")
    return problems


def score_question(answer: Any, right: Any, tol: float = TOLERANCE) -> float:
    """1 when right, 0 when wrong; a map scores the share of its keys that are right."""
    if isinstance(right, dict):
        if not isinstance(answer, dict) or not right:
            return 0.0
        return sum(close(answer.get(k), v, tol) for k, v in right.items()) / len(right)
    return float(close(answer, right, tol))


def score(answers: Any, right: dict[str, Any], tol: float = TOLERANCE) -> dict[str, float]:
    answers = answers if isinstance(answers, dict) else {}
    return {q: score_question(answers.get(q), r, tol) for q, r in right.items()}


def close(a: Any, b: float, tol: float = TOLERANCE) -> bool:
    if not _number(a):
        return False
    return abs(float(a) - b) <= tol * max(abs(b), 1e-9) or abs(float(a) - b) < 1e-9


def _number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None
