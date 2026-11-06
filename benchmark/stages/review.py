"""Review: a change on branch `feature` -> approve / request changes with findings."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from benchmark.core import Case, Grade, Stage, keyword_hit, read_json
from factory import workspace
from factory.contracts import Review


def prepare_change(case: Case, ws: Path) -> str:
    """main = base project; feature = golden product + the case's modifications (overlay)."""
    product = case.input["product"]
    workspace.copy_db(ws)
    workspace.branch(ws, "feature")
    workspace.install_product(ws, product, board=case.input.get("board", True))
    if case.input.get("overlay"):
        workspace.overlay(ws, case.resolve(case.input["overlay"]))
    workspace.commit(ws, case.input.get("commit_message", f"Add data product {product}"))
    workspace.dbt(ws, "build", "--quiet")  # db reflects the feature branch (may fail: that's the point)
    workspace.dbt(ws, "parse", "--quiet")
    return product


class ReviewStage(Stage):
    name = "review"
    agent = "review"

    def setup(self, case: Case, ws: Path) -> dict:
        shutil.copy(case.resolve(case.input["spec"]), ws / "input" / "spec.yaml")
        shutil.copy(case.resolve(case.input["pr"]), ws / "input" / "pr.md")
        product = prepare_change(case, ws)
        return {"product_id": product}

    def oracle(self, case: Case, ws: Path) -> None:
        exp = case.expected
        findings = [{"severity": "blocker", "category": d.get("category", "correctness"), "file": d["file"],
                     "message": f"{d['id']}: " + " / ".join(d["keywords"])} for d in exp.get("defects", [])]
        review = {"verdict": exp["verdict"], "summary": "oracle", "docs_up_to_date": exp.get("docs_up_to_date", True),
                  "findings": findings}
        (ws / "output" / "review.json").write_text(json.dumps(review, indent=2))

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        exp = case.expected
        path = ws / "output" / "review.json"
        if not path.exists():
            return [Grade("review_written", 0, 10, "output/review.json missing")]
        try:
            review = Review.model_validate(read_json(path))
        except Exception as exc:  # noqa: BLE001
            return [Grade("review_valid", 0, 10, str(exc)[:500])]
        grades = [Grade("review_valid", 1, 1)]

        # Verdict is what gates the line; approving a broken change is the worst outcome.
        grades.append(Grade("verdict", review.verdict == exp["verdict"], 4,
                            f"got {review.verdict}, expected {exp['verdict']}"))

        defects = exp.get("defects", [])
        serious = [f for f in review.findings if f.severity in ("blocker", "major")]
        if defects:
            found = []
            for d in defects:
                for f in review.findings:
                    same_file = d["file"].split("/")[-1] in f.file
                    if (same_file or not d.get("require_file", True)) and keyword_hit(
                            f"{f.message} {f.suggestion or ''}", d["keywords"]):
                        found.append(d["id"])
                        break
            grades.append(Grade("defect_recall", len(found) / len(defects), 3,
                                f"found {found} of {[d['id'] for d in defects]}"))
        else:
            # Clean change: every blocker/major finding is a false alarm that slows the line down.
            grades.append(Grade("no_false_alarms", 1.0 if not serious else max(0.0, 1 - 0.34 * len(serious)), 2,
                                f"{len(serious)} blocker/major findings on a clean change"))

        if "docs_up_to_date" in exp:
            grades.append(Grade("docs_check", review.docs_up_to_date == exp["docs_up_to_date"], 1,
                                f"got {review.docs_up_to_date}, expected {exp['docs_up_to_date']}"))
        return grades
