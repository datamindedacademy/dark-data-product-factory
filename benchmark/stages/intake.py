"""Intake: request -> spec. Graded on the status, the questions, and the rules the definitions mention."""

from __future__ import annotations

import shutil
from pathlib import Path

from benchmark.core import Case, Grade, Stage, keyword_hit
from factory.contracts import Spec


class Intake(Stage):
    name = "intake"
    agent = "intake"

    def setup(self, case: Case, ws: Path) -> dict:
        shutil.copy(case.resolve(case.input["issue"]), ws / "input" / "issue.md")
        return {}

    def oracle(self, case: Case, ws: Path) -> None:
        shutil.copy(case.resolve(case.expected["right_spec"]), ws / "output" / "spec.json")

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        e = case.expected
        try:
            spec = Spec.load(ws / "output" / "spec.json")
        except Exception as exc:  # noqa: BLE001
            return [Grade("valid_spec", 0, 1, f"output/spec.json missing or invalid: {str(exc)[:200]}")]
        status = e["status"] if isinstance(e["status"], list) else [e["status"]]
        grades = [Grade("status", spec.status in status, 2, f"{spec.status}, expected {' or '.join(status)}")]
        text = spec.model_dump_json().lower()
        if "questions" in e:
            got = {q.id for q in spec.questions}
            grades.append(Grade("questions", len(got & set(e["questions"])) / len(e["questions"]), 1,
                                f"has {sorted(got)}, expected {e['questions']}"))
        for m in e.get("mentions", []):  # each: {id, any: [words]}
            grades.append(Grade(m["id"], keyword_hit(text, m["any"]), 1, f"mentions one of {m['any']}"))
        return grades
