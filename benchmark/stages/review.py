"""Review: answers + code -> review.json. Graded on the verdict and on naming the planted bug."""

from __future__ import annotations

import shutil
from pathlib import Path

from benchmark.core import Case, Grade, Stage, keyword_hit
from factory.contracts import Review


class ReviewStage(Stage):
    name = "review"
    agent = "review"

    def setup(self, case: Case, ws: Path) -> dict:
        i = case.input
        shutil.copy(case.resolve(i["issue"]), ws / "input" / "issue.md")
        shutil.copy(case.resolve(i["spec"]), ws / "input" / "spec.json")
        for f in case.resolve(i["work"]).iterdir():  # the answers and the code under review
            shutil.copy(f, ws / "output" / f.name)
        return {}

    def oracle(self, case: Case, ws: Path) -> None:
        e = case.expected
        findings = [{"severity": "major", "message": " ".join(d["any"])} for d in e.get("defects", [])]
        (ws / "output" / "review.json").write_text(Review(verdict=e["verdict"], findings=findings).model_dump_json())

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        e = case.expected
        try:
            r = Review.load(ws / "output" / "review.json")
        except Exception as exc:  # noqa: BLE001
            return [Grade("valid_review", 0, 1, f"output/review.json missing or invalid: {str(exc)[:200]}")]
        grades = [Grade("verdict", r.verdict == e["verdict"], 2, f"{r.verdict}, expected {e['verdict']}")]
        text = " ".join(f.message for f in r.findings) + " " + r.summary
        for d in e.get("defects", []):  # each: {id, any: [words]}
            grades.append(Grade(d["id"], r.verdict == "request_changes" and keyword_hit(text, d["any"]), 1,
                                f"a finding mentions one of {d['any']}"))
        return grades
