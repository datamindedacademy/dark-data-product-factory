"""Artifact contracts between the stations of the factory line.

Every agent reads and writes files whose shape is defined here. Keeping the
hand-offs explicit is what lets each team build one station in isolation: the
benchmark feeds a station *golden* inputs and grades its outputs against these
models.

    issue.md ──intake──▶ spec.yaml ──implement──▶ dbt models ──review──▶ review.json
                                                     │
                                                     ├──governance──▶ governance.json
                                                     └──bi──▶ charts/<product>.yml
    runs/**/trace.jsonl ──line-manager──▶ recommendations.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- spec


class Expectation(_Model):
    """What an acceptance check's SQL must return.

    * ``matches_reference``: result equals the result of ``reference_sql`` (computed
      independently from staging/core tables). Best for the golden spec.
    * ``equals``: result's first cell equals ``value`` (within ``tolerance``).
    * ``between``: first cell lies in [min, max].
    * ``row_count``: query returns exactly ``value`` rows.
    * ``non_empty``: query returns at least one row.
    * ``empty``: query returns no rows (e.g. a "no QA accounts" check).
    """

    type: Literal["matches_reference", "equals", "between", "row_count", "non_empty", "empty"]
    value: Any | None = None
    min: float | None = None
    max: float | None = None
    reference_sql: str | None = None
    tolerance: float = Field(0.001, description="Relative tolerance for numeric comparisons")
    ordered: bool = Field(False, description="Compare rows in order (matches_reference only)")

    @model_validator(mode="after")
    def _check(self) -> "Expectation":
        need = {"matches_reference": ["reference_sql"], "equals": ["value"], "row_count": ["value"],
                "between": ["min", "max"]}
        for f in need.get(self.type, []):
            if getattr(self, f) is None:
                raise ValueError(f"expectation type {self.type!r} requires {f!r}")
        return self


class AcceptanceCheck(_Model):
    id: str
    description: str
    sql: str = Field(description="SQL against the output models. Use {{ ref('model') }} for dbt models.")
    expect: Expectation


class BusinessQuestion(_Model):
    id: str = Field(pattern=r"^Q\d+$")
    question: str
    why_it_matters: str | None = None
    metrics: list[str] = []
    dimensions: list[str] = []
    acceptance: list[AcceptanceCheck] = []


class MetricDefinition(_Model):
    name: str
    definition: str
    expression: str | None = Field(None, description="SQL expression or formula")


class ColumnSpec(_Model):
    name: str
    data_type: str | None = None
    description: str
    tests: list[str] = []
    pii: bool = False


class OutputModel(_Model):
    name: str
    description: str
    grain: list[str]
    columns: list[ColumnSpec]


class InputRef(_Model):
    name: str = Field(description="dbt model or source table, e.g. fct_orders or raw.returns")
    columns: list[str] = []
    notes: str | None = None


class DataQualityNote(_Model):
    issue: str
    handling: str


class DashboardIntent(_Model):
    title: str
    audience: str
    charts: list[str] = Field(default_factory=list, description="One line per intended chart, referencing question ids")


class DataProductSpec(_Model):
    spec_version: Literal[1] = 1
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    title: str
    status: Literal["ready", "needs_clarification", "infeasible"]
    purpose: str
    requested_by: str | None = None
    owner: str = "analytics-engineering"
    business_questions: list[BusinessQuestion] = []
    metrics: list[MetricDefinition] = []
    inputs: list[InputRef] = []
    data_quality_notes: list[DataQualityNote] = []
    outputs: list[OutputModel] = []
    dashboard: DashboardIntent | None = None
    assumptions: list[str] = []
    open_questions: list[str] = []
    infeasible_reason: str | None = None

    @model_validator(mode="after")
    def _check(self) -> "DataProductSpec":
        if self.status == "ready":
            if not self.business_questions:
                raise ValueError("a ready spec needs at least one business question")
            if not self.outputs:
                raise ValueError("a ready spec needs at least one output model")
        if self.status == "needs_clarification" and not self.open_questions:
            raise ValueError("status needs_clarification requires open_questions")
        if self.status == "infeasible" and not self.infeasible_reason:
            raise ValueError("status infeasible requires infeasible_reason")
        return self

    @classmethod
    def load(cls, path: str | Path) -> "DataProductSpec":
        return cls.model_validate(yaml.safe_load(Path(path).read_text()))


# ------------------------------------------------------------------------- review


class ReviewFinding(_Model):
    severity: Literal["blocker", "major", "minor", "nit"]
    category: Literal["correctness", "spec_mismatch", "tests", "docs", "performance", "style", "governance"]
    file: str
    line: int | None = None
    message: str
    suggestion: str | None = None


class Review(_Model):
    verdict: Literal["approve", "request_changes"]
    summary: str
    findings: list[ReviewFinding] = []
    docs_up_to_date: bool


# --------------------------------------------------------------------- governance


class GovernanceViolation(_Model):
    rule_id: str = Field(pattern=r"^GOV-\d{3}$")
    model: str
    column: str | None = None
    message: str


class GovernanceReport(_Model):
    product_id: str
    compliant: bool
    violations: list[GovernanceViolation] = []
    checked_rules: list[str] = []


# ------------------------------------------------------------------- line manager


class Recommendation(_Model):
    target_agent: Literal["intake", "implement", "review", "governance", "bi", "factory"]
    pattern: str = Field(description="The recurring problem observed")
    evidence: str = Field(description="Run ids / counts / costs that show it")
    impact: str = Field(description="Estimated cost, latency or quality impact")
    change: str = Field(description="Concrete change to prompt, skill, tool or config")
    file: str | None = Field(None, description="File in agents/ to change, if any")


class LineManagerReport(_Model):
    summary: str
    recommendations: list[Recommendation]


SCHEMAS: dict[str, type[_Model]] = {
    "spec": DataProductSpec,
    "review": Review,
    "governance": GovernanceReport,
    "line_manager": LineManagerReport,
}


def json_schema(name: str) -> dict:
    return SCHEMAS[name].model_json_schema()
