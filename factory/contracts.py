"""What the stations hand each other. The line checks these files between stations.

    intake     input/issue.md                          -> output/spec.json      (Spec)
    implement  input/spec.json (+ input/feedback.md)   -> output/answers.json   (+ the code that made it)
    review     spec, answers and code                  -> output/review.json    (Review)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Model(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Question(_Model):
    id: str = Field(description="Q1, Q2, ... as numbered in the issue")
    question: str
    answer_format: Any = Field(default="", description="The shape of the answer, as the issue asks for it")
    definition: str = Field(description="How to compute it: which data, which rules, which filters")


class Spec(_Model):
    status: Literal["ready", "needs_clarification", "infeasible"]
    questions: list[Question] = []
    assumptions: list[str] = Field(default=[], description="Choices made where the request was not explicit")
    open_questions: list[str] = Field(default=[], description="Only when status is not ready")
    reason: str = Field(default="", description="Why the request is infeasible, when it is")

    @classmethod
    def load(cls, path: Path) -> Spec:
        return cls.model_validate_json(path.read_text())


class Finding(_Model):
    question: str = Field(default="", description="Q1, Q2, ... or empty for the whole analysis")
    severity: Literal["blocker", "major", "minor"] = "major"
    message: str


class Review(_Model):
    verdict: Literal["approve", "request_changes"]
    findings: list[Finding] = []
    summary: str = ""

    @classmethod
    def load(cls, path: Path) -> Review:
        return cls.model_validate_json(path.read_text())


def json_schema(name: str) -> str:
    return json.dumps({"spec": Spec, "review": Review}[name].model_json_schema(), indent=2)
