"""Implement: answers the questions of the spec from the data."""

from pathlib import Path

from factory.agent import base_agent

HERE = Path(__file__).parent

# The message the agent gets. Yours to change, as long as the agent ends up writing output/answers.json.
TASK = """Answer the questions in input/spec.json from the data in data/.

Write the code that computes the answers to output/analysis.py (Python with duckdb) or
output/analysis.sql, run it, and write the answers to output/answers.json in the format the
request asks for (input/issue.md, section "Answers").

If input/feedback.md exists, a reviewer sent your previous answers back: fix every finding."""


# --- Your levers. Uncomment one, run the benchmark, keep it if the score goes up. ---------------

# A tool is a plain Python function: its name, arguments and docstring are what the model sees.
# This one tells the agent whether answers.json has the shape the request asks for. It needs the
# workspace, so it is made inside a function that gets it.
# def check_answers_tool(workspace):
#     def check_answers() -> str:
#         """Check output/answers.json against the format in input/issue.md. Returns the problems, or OK."""
#         from factory.answers import load, shape_problems, template
#         issue = (workspace / "input" / "issue.md").read_text()
#         return "\n".join(shape_problems(load(workspace / "output" / "answers.json"), template(issue))) or "OK"
#     return check_answers

# An MCP server, e.g. one you write that serves Fernhill's metric definitions:
# from agno.tools.mcp import MCPTools
# metrics = MCPTools(command=f"python {HERE / 'metrics_server.py'}")


def build(workspace):
    return base_agent(
        workspace,
        # Who the agent is and how it works: which tables to trust, how to join them, what to check
        # before answering (is every order counted once? do the totals add up?).
        instructions=(HERE / "instructions.md").read_text(),
        # skills=[HERE / "skills" / "fernhill-data"],    # a folder with a SKILL.md (name + description on top)
        # tools=[check_answers_tool(workspace), metrics],  # functions, Agno toolkits or MCP servers
        # model="qwen/qwen4-max",                        # any OpenRouter model; the default is small and cheap
        # effort="low",                                  # let the model reason first: low, medium or high
        # max_tool_calls=40,                             # the run stops after this many tool calls
    )
