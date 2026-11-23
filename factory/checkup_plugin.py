"""Fernhill's data product standards as a checkup plugin.

[checkup](https://pypi.org/project/checkup/) is a computational governance
framework: providers enrich a context (here: the dbt manifest via checkup-dbt),
metrics compute values from it, materializers print or store them. This module
adds one metric per *mechanical* Fernhill rule (see
``standards/data-product-standards.md``). They are registered as entry points in
``pyproject.toml``, so ``warehouse/checkup.yaml`` can use them by name::

    cd warehouse && dbt parse && checkup run                       # whole project
    checkup run --tag data_product=category_performance            # one product
    checkup run -q --materializer markdown                         # agent-friendly

Each metric's value is the number of violations; the diagnostic lists them as
``model`` or ``model.column``. GOV-006, 008 and 010 exist as heuristic metrics
too, but ``warehouse/checkup.yaml`` does not enable them: spotting PII, units and
dashboard problems is the governance agent's job, and enabling them is one of its
levers. The final's grader always applies them (``factory/tools/checkup.py``).
"""

from __future__ import annotations

import json
from typing import ClassVar

from checkup.measurement import Measurement, Measurements
from checkup.types import Context
from checkup_dbt import DbtMetric

from factory.tools.checkup import check


class FernhillRuleMetric(DbtMetric):
    """Counts violations of one Fernhill GOV rule in mart models."""

    rule_id: ClassVar[str] = ""
    unit: str = "violations"
    tags: list[str] = ["governance", "fernhill"]

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        manifest_path = self.get_project_dir(context) / "target" / "manifest.json"
        product = (context.get("tags") or {}).get("data_product")
        charts = self.get_project_dir(context) / "charts"
        findings = [f for f in check(json.loads(manifest_path.read_text()), product, charts) if f.rule_id == self.rule_id]
        items = sorted({f"{f.model}.{f.column}" if f.column else f.model for f in findings})
        diagnostic = f"{self.rule_id}: {', '.join(items)}" if items else ""
        return self.measure(value=len(findings), tags={"rule_id": self.rule_id}, diagnostic=diagnostic)


class Gov001NamingMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-001"
    name: str = "fernhill_gov001_mart_naming"
    description: str = "Mart models not named fct_* or dim_*"


class Gov002DescriptionMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-002"
    name: str = "fernhill_gov002_model_description"
    description: str = "Mart models without a description of at least 30 characters"


class Gov003ColumnDocsMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-003"
    name: str = "fernhill_gov003_column_description"
    description: str = "Mart columns without description"


class Gov004GrainMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-004"
    name: str = "fernhill_gov004_grain"
    description: str = "Mart models without meta.grain or without a test enforcing it"


class Gov005OwnershipMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-005"
    name: str = "fernhill_gov005_ownership"
    description: str = "Mart models without meta.owner or meta.data_product"


class Gov007ContractMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-007"
    name: str = "fernhill_gov007_contract"
    description: str = "Mart models without enforced contract, or columns without data_type"


class Gov009LayeringMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-009"
    name: str = "fernhill_gov009_layering"
    description: str = "Mart models selecting from source() directly"


class Gov006PiiMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-006"
    name: str = "fernhill_gov006_pii"
    description: str = "Data product columns that hold personal data (by name or meta.pii)"


class Gov008UnitsMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-008"
    name: str = "fernhill_gov008_units"
    description: str = "Ratios without an accepted_range 0..1 test, monetary columns without currency suffix"


class Gov010DashboardMetric(FernhillRuleMetric):
    rule_id: ClassVar[str] = "GOV-010"
    name: str = "fernhill_gov010_dashboard"
    description: str = "Products without a board, or board queries that do not read the product's models"
