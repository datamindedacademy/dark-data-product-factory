"""Shared building blocks for benchmark stages: cases, grades and the stage interface."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from factory import paths


@dataclass
class Grade:
    name: str
    score: float  # 0..1
    weight: float = 1.0
    detail: str = ""

    def __post_init__(self) -> None:
        self.score = max(0.0, min(1.0, float(self.score)))


@dataclass
class Case:
    id: str
    stage: str
    description: str
    input: dict[str, Any]
    expected: dict[str, Any]
    path: Path
    tags: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "Case":
        raw = yaml.safe_load(path.read_text())
        return cls(path=path, tags=raw.pop("tags", []), **raw)

    def resolve(self, rel: str) -> Path:
        """Resolve a path from a case file: relative to the case file, else to benchmark/."""
        p = (self.path.parent / rel)
        return p if p.exists() else paths.BENCHMARK / rel


def weighted(grades: list[Grade]) -> float:
    total = sum(g.weight for g in grades)
    return sum(g.score * g.weight for g in grades) / total if total else 0.0


def grades_json(grades: list[Grade]) -> list[dict]:
    return [asdict(g) for g in grades]


def load_cases(stage: str, suite: Path | None = None, only: list[str] | None = None) -> list[Case]:
    root = (suite or paths.CASES) / stage
    cases = [Case.load(p) for p in sorted(root.glob("*.yaml"))]
    if only:
        cases = [c for c in cases if c.id in only or any(c.id.startswith(o) for o in only)]
    return cases


class Stage:
    """Interface every benchmark stage implements."""

    name: str
    agent: str  # default agent dir under agents/

    def setup(self, case: Case, ws: Path) -> dict[str, Any]:
        """Prepare the workspace for the case; return template variables for the agent prompt."""
        raise NotImplementedError

    def oracle(self, case: Case, ws: Path) -> None:
        """Write the golden output into the workspace (validates the graders, no LLM needed)."""
        raise NotImplementedError

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        raise NotImplementedError


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def keyword_hit(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in keywords)
