"""Review: checks the answers and the code before they go back to the requester."""

from pathlib import Path

from factory.agent import base_agent
from factory.contracts import json_schema

HERE = Path(__file__).parent

TASK = f"""Review the answers in output/answers.json and the code in output/ that produced them,
against the spec in input/spec.json and the request in input/issue.md.

Write output/review.json in this format:

{json_schema("review")}

Request changes only for problems that make an answer wrong or missing."""


def build(workspace):
    return base_agent(workspace, instructions=(HERE / "instructions.md").read_text())
