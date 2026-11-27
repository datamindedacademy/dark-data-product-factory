"""Intake: turns the request into a spec that says how to answer each question."""

from pathlib import Path

from factory.agent import base_agent
from factory.contracts import json_schema

HERE = Path(__file__).parent

TASK = f"""Read the request in input/issue.md. Write output/spec.json in this format:

{json_schema("spec")}

One entry in "questions" per numbered question of the request, with its id (Q1, Q2, ...).
Set "status" to "ready" when the data can answer every question."""


def build(workspace):
    return base_agent(workspace, instructions=(HERE / "instructions.md").read_text())
