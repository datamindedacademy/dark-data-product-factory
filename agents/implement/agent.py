"""Implement: answers the questions of the spec from the data."""

from pathlib import Path

from factory.agent import base_agent

HERE = Path(__file__).parent

TASK = """Answer the questions in input/spec.json from the data in data/.

Write the code that computes the answers to output/analysis.py (Python with duckdb) or
output/analysis.sql, run it, and write the answers to output/answers.json in the format the
request asks for (input/issue.md, section "Answers").

If input/feedback.md exists, a reviewer sent your previous answers back: fix every finding."""


def build(workspace):
    return base_agent(workspace, instructions=(HERE / "instructions.md").read_text())
