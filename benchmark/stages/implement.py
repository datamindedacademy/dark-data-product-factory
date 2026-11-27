"""Implement: spec -> answers.json. Graded per question against the right answers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from benchmark.core import Case, Grade, Stage
from factory import answers


class Implement(Stage):
    name = "implement"
    agent = "implement"

    def setup(self, case: Case, ws: Path) -> dict:
        shutil.copy(case.resolve(case.input["issue"]), ws / "input" / "issue.md")
        shutil.copy(case.resolve(case.input["spec"]), ws / "input" / "spec.json")
        return {}

    def oracle(self, case: Case, ws: Path) -> None:
        shutil.copy(case.resolve(case.expected["answers"]), ws / "output" / "answers.json")

    def grade(self, case: Case, ws: Path, judge: bool = False) -> list[Grade]:
        right = json.loads(case.resolve(case.expected["answers"]).read_text())
        given = answers.load(ws / "output" / "answers.json")
        if given is None:
            return [Grade("answers", 0, 1, "output/answers.json missing or not JSON")]
        return [Grade(q, s, 1, f"{s:.0%} of the values within {answers.TOLERANCE:.1%}")
                for q, s in answers.score(given, right).items()]
