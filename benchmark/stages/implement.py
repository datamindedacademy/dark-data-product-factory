"""Implement: executable spec -> dbt models that pass the acceptance checks."""

from __future__ import annotations

from pathlib import Path

import duckdb
import yaml

from benchmark.core import Case, Grade, Stage
from factory import workspace
from factory.acceptance import AcceptanceReport, evaluate
from factory.contracts import DataProductSpec
from factory.tools import checkup


class Implement(Stage):
    name = "implement"
    agent = "implement"

    def _golden(self, case: Case) -> DataProductSpec:
        return DataProductSpec.load(case.resolve(case.input["spec"]))

    def setup(self, case: Case, ws: Path) -> dict:
        spec = self._golden(case)
        hidden = set(case.expected.get("hidden_checks", []))
        data = spec.model_dump(mode="json", exclude_none=True)
        for q in data["business_questions"]:
            q["acceptance"] = [a for a in q["acceptance"] if a["id"] not in hidden]
        (ws / "input" / "spec.yaml").write_text(yaml.safe_dump(data, sort_keys=False, width=120))
        workspace.copy_db(ws)
        return {"product_id": spec.id}

    def oracle(self, case: Case, ws: Path) -> None:
        workspace.install_product(ws, self._golden(case).id, board=False)
        workspace.dbt(ws, "build", "--quiet")

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        spec = self._golden(case)
        grades: list[Grade] = []

        product_dir = ws / "warehouse" / "models" / "marts" / spec.id
        if not any(product_dir.glob("*.sql")):
            return [Grade("models_written", 0, 10, f"no models in warehouse/models/marts/{spec.id}/")]
        build = workspace.dbt(ws, "build")
        tail = (build.stdout or "").strip().splitlines()[-1:] or [""]
        grades.append(Grade("dbt_build", build.returncode == 0, 2, tail[0][:300]))

        db = ws / "warehouse" / "warehouse.duckdb"
        con = duckdb.connect(str(db), read_only=True)
        try:
            cols = {}
            for t, c in con.execute("select table_name, column_name from information_schema.columns "
                                    "where table_schema = 'main'").fetchall():
                cols.setdefault(t, set()).add(c)
            missing = []
            expected_cols = 0
            for out in spec.outputs:
                for c in out.columns:
                    expected_cols += 1
                    if c.name not in cols.get(out.name, set()):
                        missing.append(f"{out.name}.{c.name}")
            grades.append(Grade("outputs_match_spec", 1 - len(missing) / max(expected_cols, 1), 2,
                                f"missing {missing}" if missing else "all output models and columns exist"))

            hidden = set(case.expected.get("hidden_checks", []))
            visible, secret = AcceptanceReport(), AcceptanceReport()
            for q in spec.business_questions:
                for chk in q.acceptance:
                    (secret if chk.id in hidden else visible).results.append(evaluate(con, chk))
        finally:
            con.close()
        grades.append(Grade("acceptance_visible", visible.score, 4, visible.as_text()))
        if secret.total:
            grades.append(Grade("acceptance_hidden", secret.score, 3, secret.as_text()))

        workspace.dbt(ws, "parse", "--quiet")
        try:
            result = checkup.run(ws / "warehouse", spec.id)
            n = len(result["violations"])
            detail = "; ".join(f"{v['rule_id']} {v['model']} {v['column'] or ''}" for v in result["violations"][:10])
            grades.append(Grade("standards_checkup", max(0.0, 1 - n / 5), 2, f"{n} violations. {detail}"))
        except FileNotFoundError as exc:
            grades.append(Grade("standards_checkup", 0, 2, str(exc)))
        return grades
