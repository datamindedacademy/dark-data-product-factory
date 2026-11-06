"""Governance: data product -> list of standards violations (rule id x model)."""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.core import Case, Grade, Stage, read_json
from benchmark.stages.review import prepare_change
from factory.contracts import GovernanceReport


PRODUCT_LEVEL = {"GOV-010"}


def _key(rule_id: str, model: str) -> tuple[str, str]:
    """Violations are matched on (rule, model); product-level rules on the rule alone."""
    return (rule_id, "*") if rule_id in PRODUCT_LEVEL else (rule_id, model)


class Governance(Stage):
    name = "governance"
    agent = "governance"

    def setup(self, case: Case, ws: Path) -> dict:
        return {"product_id": prepare_change(case, ws)}

    def oracle(self, case: Case, ws: Path) -> None:
        exp = case.expected
        report = {"product_id": case.input["product"], "compliant": not exp["violations"],
                  "checked_rules": [f"GOV-{i:03d}" for i in range(1, 12)],
                  "violations": [{**v, "message": "oracle"} for v in exp["violations"]]}
        (ws / "output" / "governance.json").write_text(json.dumps(report, indent=2))

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        exp = case.expected
        path = ws / "output" / "governance.json"
        if not path.exists():
            return [Grade("report_written", 0, 10, "output/governance.json missing")]
        try:
            report = GovernanceReport.model_validate(read_json(path))
        except Exception as exc:  # noqa: BLE001
            return [Grade("report_valid", 0, 10, str(exc)[:500])]
        grades = [Grade("report_valid", 1, 1)]

        expected = {_key(v["rule_id"], v["model"]) for v in exp["violations"]}
        got = {_key(v.rule_id, v.model) for v in report.violations}
        tp = expected & got
        fp = got - expected - {_key(*x) for x in exp.get("acceptable_extra", [])}
        fn = expected - got
        if expected:
            recall = len(tp) / len(expected)
            precision = len(tp) / (len(tp) + len(fp)) if (tp or fp) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            grades.append(Grade("violations_f1", f1, 5,
                                f"recall {recall:.2f} precision {precision:.2f}; missed {sorted(fn)}; false {sorted(fp)}"))
            mech = {k for k in expected if k[0] in ("GOV-001", "GOV-002", "GOV-003", "GOV-004", "GOV-005", "GOV-007", "GOV-009")}
            judg = expected - mech
            if judg:
                grades.append(Grade("judgement_rules_recall", len(judg & got) / len(judg), 3,
                                    f"rules needing judgement found: {sorted(judg & got)} of {sorted(judg)}"))
        else:
            grades.append(Grade("no_false_violations", max(0.0, 1 - 0.25 * len(fp)), 5, f"false violations: {sorted(fp)}"))
        grades.append(Grade("compliant_flag", report.compliant == (not expected), 1,
                            f"got compliant={report.compliant}"))
        return grades
