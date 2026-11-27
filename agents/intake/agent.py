"""Intake: turns the request into a spec that says how to answer each question."""

from pathlib import Path

from factory.agent import base_agent
from factory.contracts import json_schema

HERE = Path(__file__).parent

# The message the agent gets. Yours to change, as long as the agent ends up writing output/spec.json.
TASK = f"""Read the request in input/issue.md. Write output/spec.json in this format:

{json_schema("spec")}

One entry in "questions" per numbered question of the request, with its id (Q1, Q2, ...).
Set "status" to "ready" when the data can answer every question."""


# --- Your levers. Uncomment one, run the benchmark, keep it if the score goes up. ---------------

# A tool is a plain Python function: its name, arguments and docstring are what the model sees.
# This one gives an overview of the data in one call. It needs the workspace, so it is made inside
# a function that gets it.
# def list_tables_tool(workspace):
#     def list_tables() -> str:
#         """List the tables in data/ with their columns."""
#         return "\n".join(f"{f.stem}: {f.open().readline().strip()}" for f in sorted((workspace / "data").glob("*.csv")))
#     return list_tables


def build(workspace):
    return base_agent(
        workspace,
        # Who the agent is and how it works. Fernhill's rules from the interviews could go here,
        # or in a skill so implement and review can share them.
        instructions=(HERE / "instructions.md").read_text(),
        # skills=[HERE / "skills" / "fernhill-rules"],   # a folder with a SKILL.md (name + description on top)
        # tools=[list_tables_tool(workspace)],           # functions, Agno toolkits or MCPTools(command="...")
        # model="qwen/qwen4-max",                        # any OpenRouter model; the default is small and cheap
        # effort="low",                                  # let the model reason first: low, medium or high
        # max_tool_calls=40,                             # the run stops after this many tool calls
    )
