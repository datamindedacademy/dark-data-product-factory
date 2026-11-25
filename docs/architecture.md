# Architecture

## The line

```
                ┌──────────── factory e2e (factory/e2e.py) ─────────────┐
 input/issue.md │ intake ─▶ output/spec.yaml                             │
                │   status != ready ─▶ stop: open questions to requester │
                │ implement (branch feature) ─▶ models/marts/<id>/        │
                │ review ─▶ output/review.json      ┐                    │
                │ governance ─▶ output/governance.json ├─▶ findings ─▶ input/feedback.md ─▶ implement (rework)
                │ bi ─▶ charts/<id>.yml ─▶ renders/<id>.html             │
                └────────────────────────────────────────────────────────┘
 every station ─▶ runs/<run>/<station>-<n>/{prompt.txt, trace.jsonl, summary.json} ─▶ line manager
```

The same stations run as a GitHub Actions pipeline (`factory ci <station>`, see
[ci.md](ci.md)); `factory e2e` is the laptop version of that pipeline, and the line the final
challenge runs ([competition.md](competition.md)).

## Contracts (`factory/contracts.py`)

| Artifact | Model | Written by | Read by |
|---|---|---|---|
| `output/spec.yaml` | `DataProductSpec` | intake | implement, review, bi, graders |
| `warehouse/models/marts/<id>/*` | dbt models + `_<id>.yml` | implement | review, governance, bi |
| `output/review.json` | `Review` | review | e2e (rework loop) |
| `output/governance.json` | `GovernanceReport` | governance | e2e (rework loop) |
| `warehouse/charts/<id>.yml` | dbt charts board | bi | humans |
| `output/recommendations.json` | `LineManagerReport` | line manager | humans |

`factory validate <kind> <file>` validates any of them; agents are told to run it.

`DataProductSpec` is a home-grown format on purpose: it is small enough to read in one go. Its
`outputs` are a data contract, and its `metrics` a semantic model. The open standards for the two are
[ODCS](https://bitol-io.github.io/open-data-contract-standard/) (Open Data Contract Standard, Bitol /
Linux Foundation: schema, quality rules, SLAs, ownership of an output port) and
[Apache Ossie](https://ossie.apache.org/) (metrics, dimensions and their relationships). Emitting
both next to `spec.yaml` is a good extension: consumers outside the factory can read them, and
ODCS quality rules can run in CI with tools like `datacontract-cli`.

### The spec is executable

Each business question carries **acceptance checks**: SQL against the output models
plus an expectation (`equals`, `between`, `row_count`, `non_empty`, `empty`, or
`matches_reference` - the result must equal a reference query written against the
staging/core layer). `factory accept spec.yaml --db warehouse/warehouse.duckdb` runs
them (`factory/acceptance.py`). Intake writes them, implement makes them pass, the
benchmark grades with them, and the e2e line reports them. The golden specs in
`benchmark/products/*/spec.yaml` show what good checks look like.

## Workspaces (`factory/workspace.py`)

Every run gets a fresh copy of the company repo in `runs/<run-id>/workspace/`: the dbt
project with its own DuckDB file, the standards, `input/`, `output/`, and the agent's
skills under `.claude/skills/`. It is a git repo (`main` = base project). Runs never
touch `warehouse/` in the repo root, so they can run in parallel and be inspected
afterwards (`cd runs/<run>/workspace && git log -p`).

## Agents and the runner (`factory/runner.py`)

An agent is a directory (see [agents/README.md](../agents/README.md)). Everything around the
runner (the e2e line, the CI stations, the benchmark, the final scoring) only knows
`run_agent(agent_dir, workspace, run_dir) -> summary` and the files the agent leaves behind, so
the framework is a detail of the agent directory:

Every agent is an [Agno](https://docs.agno.com) agent.

- **`agent.py` present →** the runner calls `build_agent(ws, cfg)`. Tools, skills and MCP servers
  are whatever `agent.py` gives the `Agent`.
- **otherwise →** the runner builds one from `agent.yaml` (`default_agent` in `factory/runner.py`):

| agent.yaml | Agno |
|---|---|
| `model`, `effort` | `OpenRouter(id=model, reasoning_effort=effort)` (`factory/llm.py`) |
| `max_turns` | `tool_call_limit` |
| `system_prompt` (+ `CLAUDE.md`) | `instructions` |
| `builtin_tools` | `FileTools(base_dir=workspace)` for Read, Write, Edit, Glob and Grep; a `bash` tool for Bash |
| `mcp` | the `warehouse` and `governance` functions from `factory/tools/`, or `MCPTools` for dbt charts' `dct` server |
| `skills` | `Skills(loaders=[LocalSkills(...)])` for each listed `agents/<x>/skills/<name>` |
| `tools.py` | extra tools: `build_tools(ws)` returning plain functions |

Every agent, also one from `agent.py`, gets a tool hook that refuses calls reaching outside the
workspace (the repository holds the golden answers), and blocking tools run in a thread so review
and governance really run in parallel.

## Traces (`factory/tracing.py`)

`trace.jsonl` has one event per assistant text, tool call and tool result, plus `result`
(cost, turns, tokens). `summary.json` aggregates it and the benchmark adds `score` and `grades`.
The line manager reads exactly these files. The events are written when the run ends, so they all
carry the end time. The cost is what OpenRouter reports for the run, the same way for every team and model.

## Tools (`factory/tools/`)

- `warehouse`: `run_sql` (read-only), `list_tables`, `describe_table` - bound to the
  workspace's DuckDB. Baselines only get `run_sql`. `run_sql_text` is the same query as a plain
  function, for Agno agents.
- `governance`: `checkup` - runs [checkup](https://pypi.org/project/checkup/)
  (`checkup run`, config in `warehouse/checkup.yaml`): project health metrics from the
  checkup-dbt plugin plus one metric per mechanical Fernhill rule (GOV-001..005, 007, 009)
  from our own plugin in `factory/checkup_plugin.py`, registered as `checkup.metrics` entry
  points in `pyproject.toml`. `--tag data_product=<id>` scopes the Fernhill rules to one
  product. Also available as `factory checkup [--product <id>] [--json]`. The other rules
  need judgement.
- `dct` (external): `dct mcp serve`, dbt charts' own MCP server with schema browsing,
  validation, rendering and its authoring skills.
