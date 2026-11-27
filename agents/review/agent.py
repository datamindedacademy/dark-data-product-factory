"""Review: checks the answers and the code before they go back to the requester."""

from pathlib import Path

from factory.agent import base_agent
from factory.contracts import json_schema

HERE = Path(__file__).parent

# The message the agent gets. Yours to change, as long as the agent ends up writing output/review.json.
TASK = f"""Review the answers in output/answers.json and the code in output/ that produced them,
against the spec in input/spec.json and the request in input/issue.md.

Write output/review.json in this format:

{json_schema("review")}

Request changes only for problems that make an answer wrong or missing."""


# --- Your levers. Uncomment one, run the benchmark, keep it if the score goes up. ---------------

# A tool is a plain Python function: its name, arguments and docstring are what the model sees.
# This one hands the reviewer a checklist of the mistakes your benchmark keeps finding (write it
# yourself, in checklist.md next to this file). Instructions or a skill can carry it too.
# def checklist() -> str:
#     """The mistakes to check for in every review, one per line."""
#     return (HERE / "checklist.md").read_text()


def build(workspace):
    return base_agent(
        workspace,
        instructions=(HERE / "instructions.md").read_text(),
        # skills=[HERE / "skills" / "review-checklist"],  # a folder with a SKILL.md (name + description on top)
        # tools=[checklist],                              # functions, Agno toolkits or MCPTools(command="...")
        # model="qwen/qwen4-max",                         # a second opinion from another model can catch more
        # effort="low",                                   # let the model reason first: low, medium or high
        # max_tool_calls=40,                              # the run stops after this many tool calls
    )
