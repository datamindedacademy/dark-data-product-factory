"""Line manager: traces of many runs -> recommendations that remove recurring waste."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

from benchmark.core import Case, Grade, Stage, keyword_hit, read_json
from factory import paths
from factory.contracts import LineManagerReport


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("lm_generate_runs", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


class LineManager(Stage):
    name = "line_manager"
    agent = "line_manager"

    def setup(self, case: Case, ws: Path) -> dict:
        runs = ws / "input" / "runs"
        if "generator" in case.input:
            _load_generator(case.resolve(case.input["generator"])).main(runs, seed=case.input.get("seed", 7))
        else:
            shutil.copytree(case.resolve(case.input["runs"]), runs)
        shutil.copytree(paths.AGENTS, ws / "agents", ignore=shutil.ignore_patterns("__pycache__"))
        return {}

    def oracle(self, case: Case, ws: Path) -> None:
        recs = []
        for p in case.expected["patterns"]:
            words = " ".join(group[0] for group in p["all_of"])
            recs.append({"target_agent": p["targets"][0], "pattern": words, "evidence": "oracle", "impact": "oracle",
                         "change": words, "file": p.get("file")})
        (ws / "output" / "recommendations.json").write_text(json.dumps({"summary": "oracle", "recommendations": recs}))

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        path = ws / "output" / "recommendations.json"
        if not path.exists():
            return [Grade("recommendations_written", 0, 10, "output/recommendations.json missing")]
        try:
            report = LineManagerReport.model_validate(read_json(path))
        except Exception as exc:  # noqa: BLE001
            return [Grade("recommendations_valid", 0, 10, str(exc)[:500])]
        grades = [Grade("recommendations_valid", 1, 1)]

        found = []
        for p in case.expected["patterns"]:
            for r in report.recommendations:
                text = f"{r.pattern} {r.evidence} {r.change} {r.file or ''}"
                if r.target_agent in p["targets"] and all(keyword_hit(text, g) for g in p["all_of"]):
                    found.append(p["id"])
                    break
        n = len(case.expected["patterns"])
        grades.append(Grade("pattern_recall", len(found) / n, 5,
                            f"found {found} of {[p['id'] for p in case.expected['patterns']]}"))

        with_file = [r for r in report.recommendations if r.file]
        existing = [r for r in with_file if (ws / r.file).exists() or (ws / r.file).parent.exists()]
        grades.append(Grade("actionable", len(existing) / len(report.recommendations) if report.recommendations else 0, 1,
                            f"{len(existing)}/{len(report.recommendations)} recommendations point at a file in agents/"))
        limit = case.expected.get("max_recommendations", 10)
        grades.append(Grade("focused", 1.0 if len(report.recommendations) <= limit else limit / len(report.recommendations), 1,
                            f"{len(report.recommendations)} recommendations (limit {limit})"))

        if judge:
            from factory.judge import judge as llm_judge

            md = (ws / "output" / "report.md").read_text() if (ws / "output" / "report.md").exists() else ""
            score, detail = llm_judge(
                "Analyse a week of agent runs and recommend changes that reduce cost, latency and rework.",
                md + "\n\n" + path.read_text(),
                ["Recommendations are backed by quantified evidence from the traces",
                 "Recommendations are prioritised by impact",
                 "Each change is concrete enough to implement in an hour"])
            grades.append(Grade("judge_quality", score, 2, detail))
        return grades
