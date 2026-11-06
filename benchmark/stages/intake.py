"""Intake: GitHub issue -> executable spec."""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb
import yaml

from benchmark.core import Case, Grade, Stage, keyword_hit
from factory.acceptance import render_sql
from factory.contracts import DataProductSpec


def _spec_text(spec: DataProductSpec) -> str:
    return yaml.safe_dump(spec.model_dump(mode="json"), sort_keys=False)


class Intake(Stage):
    name = "intake"
    agent = "intake"

    def setup(self, case: Case, ws: Path) -> dict:
        shutil.copy(case.resolve(case.input["issue"]), ws / "input" / "issue.md")
        return {}

    def oracle(self, case: Case, ws: Path) -> None:
        shutil.copy(case.resolve(case.expected["oracle_spec"]), ws / "output" / "spec.yaml")

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        exp = case.expected
        path = ws / "output" / "spec.yaml"
        if not path.exists():
            return [Grade("spec_written", 0, 10, "output/spec.yaml missing")]
        try:
            spec = DataProductSpec.load(path)
        except Exception as exc:  # noqa: BLE001
            return [Grade("spec_valid", 0, 10, f"invalid spec: {str(exc)[:500]}")]
        text = _spec_text(spec)
        grades = [Grade("spec_valid", 1, 1)]

        allowed = exp["status"] if isinstance(exp["status"], list) else [exp["status"]]
        grades.append(Grade("status", spec.status in allowed, 3, f"got {spec.status}, expected {allowed}"))

        # Data traps the analyst should have found (deterministic keyword match).
        traps = exp.get("traps", [])
        if traps:
            found = [t["id"] for t in traps if keyword_hit(text, t["keywords"])]
            missed = [t["id"] for t in traps if t["id"] not in found]
            grades.append(Grade("data_traps", len(found) / len(traps), 3, f"found {found}, missed {missed}"))

        # Questions the stakeholder needs answered.
        qs = exp.get("questions", [])
        if qs:
            q_text = " ".join(q.question + " " + " ".join(q.metrics + q.dimensions) for q in spec.business_questions)
            hit = [q["id"] for q in qs if all(keyword_hit(q_text, alt) for alt in q["all_of"])]
            grades.append(Grade("question_coverage", len(hit) / len(qs), 2,
                                f"covered {hit} of {[q['id'] for q in qs]}"))

        # Inputs must exist in the warehouse; reference SQL must run.
        grades.append(self._grounding(spec, ws))

        if spec.status == "ready":
            n_q = len(spec.business_questions)
            with_checks = sum(1 for q in spec.business_questions if q.acceptance)
            grades.append(Grade("acceptance_checks", with_checks / n_q if n_q else 0, 2,
                                f"{with_checks}/{n_q} questions have executable acceptance checks"))
        elif exp.get("reason_keywords"):
            reason = " ".join(filter(None, [spec.infeasible_reason, *spec.open_questions, *spec.assumptions]))
            grades.append(Grade("explains_blocker", keyword_hit(reason, exp["reason_keywords"]), 2,
                                "reason mentions " + str(exp["reason_keywords"])))
            grades.append(Grade("no_fabricated_outputs", not spec.outputs or spec.status != "infeasible", 1))

        if judge:
            from factory.judge import judge as llm_judge

            issue = (ws / "input" / "issue.md").read_text()
            score, detail = llm_judge(
                f"Write a data product spec for this request:\n{issue}", text,
                ["The purpose states who uses the product and which decision it supports",
                 "Business questions are specific and answerable with the available data",
                 "Metrics have unambiguous definitions (filters, currency, attribution)",
                 "Acceptance checks would catch a wrong implementation",
                 "Ambiguities are resolved explicitly as assumptions or open questions"])
            grades.append(Grade("judge_quality", score, 3, detail))
        return grades

    @staticmethod
    def _grounding(spec: DataProductSpec, ws: Path) -> Grade:
        db = ws / "warehouse" / "warehouse.duckdb"
        con = duckdb.connect(str(db), read_only=True)
        try:
            cols = con.execute("select table_schema, table_name, column_name from information_schema.columns").fetchall()
            tables: dict[str, set[str]] = {}
            for schema, t, c in cols:
                tables.setdefault(t, set()).add(c)
                tables.setdefault(f"{schema}.{t}", set()).add(c)
            problems, checked = [], 0
            for inp in spec.inputs:
                name = inp.name.replace("source:", "").strip()
                checked += 1
                if name not in tables:
                    problems.append(f"unknown input {name}")
                    continue
                bad = [c for c in inp.columns if c not in tables[name]]
                if bad:
                    problems.append(f"{name}: unknown columns {bad}")
            for q in spec.business_questions:
                for chk in q.acceptance:
                    if chk.expect.reference_sql:
                        checked += 1
                        try:
                            con.execute(render_sql(chk.expect.reference_sql)).fetchall()
                        except Exception as exc:  # noqa: BLE001
                            problems.append(f"{chk.id} reference_sql fails: {str(exc).splitlines()[0][:120]}")
        finally:
            con.close()
        if not checked:
            return Grade("grounding", 0.5, 2, "no inputs listed")
        return Grade("grounding", 1 - len(problems) / checked, 2, "; ".join(problems) or "all inputs exist")
