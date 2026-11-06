"""BI: spec + built mart models -> dbt charts board that answers every business question."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import yaml

from benchmark.core import Case, Grade, Stage
from factory import paths, workspace
from factory.contracts import DataProductSpec

_QID = re.compile(r"\bQ\d+\b")


def _layout_charts(node) -> set[str]:
    """Chart names placed anywhere in the board layout."""
    out: set[str] = set()
    if isinstance(node, str):
        out.add(node)
    elif isinstance(node, list):
        for x in node:
            out |= _layout_charts(x)
    elif isinstance(node, dict):
        for k in ("rows", "cols", "items", "chart"):
            if k in node:
                out |= _layout_charts(node[k])
        if "tabs" in node:
            out |= _layout_charts(node["tabs"])
    return out


class BI(Stage):
    name = "bi"
    agent = "bi"

    def _spec(self, case: Case) -> DataProductSpec:
        return DataProductSpec.load(case.resolve(case.input["spec"]))

    def setup(self, case: Case, ws: Path) -> dict:
        spec = self._spec(case)
        shutil.copy(case.resolve(case.input["spec"]), ws / "input" / "spec.yaml")
        workspace.copy_db(ws)
        workspace.install_product(ws, spec.id, board=False)
        workspace.commit(ws, f"Add data product {spec.id}")
        workspace.dbt(ws, "build", "--quiet")
        return {"product_id": spec.id}

    def oracle(self, case: Case, ws: Path) -> None:
        spec = self._spec(case)
        shutil.copy(paths.PRODUCTS / spec.id / "board.yml", ws / "warehouse" / "charts" / f"{spec.id}.yml")

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        spec = self._spec(case)
        rel = f"charts/{spec.id}.yml"
        board_path = ws / "warehouse" / rel
        if not board_path.exists():
            return [Grade("board_written", 0, 10, f"warehouse/{rel} missing")]
        grades = []

        val = workspace.dct(ws, "validate", rel)
        grades.append(Grade("dct_validate", val.returncode == 0, 2, (val.stdout + val.stderr).strip()[-400:]))

        render = workspace.dct(ws, "render", rel, "--format", "text-data", "--no-cache", "--no-warnings")
        grades.append(Grade("dct_render", render.returncode == 0, 2,
                            "renders without chart errors" if render.returncode == 0 else render.stderr.strip()[-400:]))

        try:
            board = yaml.safe_load(board_path.read_text()) or {}
        except yaml.YAMLError as exc:
            return grades + [Grade("board_yaml", 0, 4, str(exc)[:300])]
        queries = board.get("queries") or {}
        charts = board.get("charts") or {}
        placed = _layout_charts({k: board[k] for k in ("rows", "cols", "grid", "tabs") if k in board})

        # Coverage: every question is answered by a query (notes) used by a chart placed on the board.
        answered: set[str] = set()
        for cname, chart in charts.items():
            if cname not in placed or not isinstance(chart, dict):
                continue
            q = chart.get("query")
            qdef = queries.get(q) if isinstance(q, str) else None
            notes = (qdef.get("notes", "") if isinstance(qdef, dict) else "") + " " + str(chart.get("title", ""))
            answered |= set(_QID.findall(notes))
        wanted = {q.id for q in spec.business_questions}
        grades.append(Grade("question_coverage", len(wanted & answered) / len(wanted), 3,
                            f"answered {sorted(wanted & answered)} of {sorted(wanted)}"))

        # Lineage: queries should read the product's mart models, not raw/staging tables.
        outputs = {o.name for o in spec.outputs}
        sqls = [q.get("sql", "") if isinstance(q, dict) else str(q) for q in queries.values()]
        on_product = sum(1 for s in sqls if any(o in s for o in outputs))
        off = sum(1 for s in sqls if re.search(r"\b(raw\.|stg_)", s))
        lineage = (on_product / len(sqls) if sqls else 0) * (0.5 if off else 1)
        grades.append(Grade("reads_product_models", lineage, 1,
                            f"{on_product}/{len(sqls)} queries read {sorted(outputs)}; {off} read raw/staging"))

        if judge and render.returncode == 0:
            from factory.judge import judge as llm_judge

            qs = "\n".join(f"{q.id}: {q.question}" for q in spec.business_questions)
            score, detail = llm_judge(
                f"Build a dashboard answering these questions for {spec.dashboard.audience if spec.dashboard else 'stakeholders'}:\n{qs}",
                f"Rendered dashboard (text + data):\n{render.stdout[:30000]}",
                [f"The dashboard lets the user answer {q.id}: {q.question}" for q in spec.business_questions]
                + ["Chart types fit the data (trends as lines, comparisons as bars, single numbers as KPIs)",
                   "Titles and labels are understandable for a business user"])
            grades.append(Grade("judge_answers_questions", score, 3, detail))
        return grades
