# Agents

One folder per station. `agents/line.yaml` lists the stations the line runs and how many rework
rounds it allows. The final runs this folder from your fork.

## How to work

Start with **one agent**, the one where the most points are. Work in a copy so you can compare:

```bash
cp -r agents/implement agents/implement-ourteam
```

1. **Benchmark.** Add a case of your own in `benchmark/cases/<station>/`, then run
   `factory bench run implement --agent agents/implement-ourteam --label v1 --repeat 3`
2. **Traces.** Open the runs that lost points in Phoenix (http://localhost:6006), or read
   `runs/bench-…/<case>-r<n>/trace.jsonl`. What went wrong?
3. **Context.** Change one thing: the instructions, a skill, a tool, an MCP server, the model.
4. **Repeat.** Run the benchmark again (`--label v2`) and compare with `factory bench report`.
   Better: keep it. Worse: undo it.

When the agent stops improving, copy it back and take the next one:

```bash
rm -rf agents/implement && cp -r agents/implement-ourteam agents/implement
```

## What an agent is

```
agents/<station>/
  agent.py           TASK (the message the agent gets) and build(workspace) -> an Agno agent
  instructions.md    who the agent is and how it works
  README.md          what the station is responsible for, and hints
```

Every baseline starts from the same base agent:

```python
from factory.agent import base_agent

TASK = "Answer the questions in input/spec.json ..."

def build(workspace):
    return base_agent(workspace, instructions=(HERE / "instructions.md").read_text())
```

Each `agent.py` has the levers in it, commented out: a skill, a tool (with a working example for
that station), an MCP server, another model, reasoning. Uncomment one, run the benchmark, keep it if
the score goes up.

The base agent can read and write files, run shell commands (Python with duckdb and pandas) and
query the CSV files with SQL (`run_sql`), all inside its workspace. Its keyword arguments are your
levers:

```python
base_agent(
    workspace,
    instructions="...",                       # more context: Fernhill's rules, a checklist, examples
    skills=[HERE / "skills" / "fernhill"],    # folders with a SKILL.md, loaded when the agent needs them
    tools=[my_function, MCPTools(command="...")],  # Python functions, Agno toolkits, an MCP server
    model="qwen/qwen4-max",                   # any OpenRouter model
    effort="low",                             # reasoning before answering: low, medium or high
    max_tool_calls=40,
)
```

- **A skill** is a folder with a `SKILL.md` that starts with `name` and `description` front matter.
- **An MCP server:** `from agno.tools.mcp import MCPTools`, then `MCPTools(command="python server.py")`
  in `tools`. Agno starts and stops it for each run.
- **Reasoning** shows up in the traces (Phoenix and `trace.jsonl`), and costs tokens.
- You can also build the Agno agent yourself in `build()`: the runner only needs `.arun(TASK)`.

Every agent gets a hook that refuses tool calls outside its workspace. Python packages are those in
`pyproject.toml`: the final installs the organisers' lock file, not yours.

## Adding a station

Add a folder with an `agent.py` and list it in `agents/line.yaml`:

- **before `implement`** it runs once, in order. For example a data explorer that writes notes to
  `input/` for implement.
- **after `implement`** it is a checker, like review. It runs side by side with the other checkers
  and writes `output/<name>.json` in the review format (`factory schema review`). Its findings go
  back to implement.

A station costs money and minutes on every run. Add one when the benchmark says it pays off.
