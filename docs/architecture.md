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

- **`agent.py` present → an Agno agent.** The runner calls `build_agent(ws, cfg)` and
  `await agent.arun(prompt)`. Tools, skills and MCP servers are whatever `agent.py` gives the
  Agno `Agent`; `builtin_tools` and `mcp` in `agent.yaml` are ignored. `max_budget_usd` is not
  enforced.
- **otherwise → the Claude Agent SDK** (the baselines). The runner turns `agent.yaml` into
  `ClaudeAgentOptions`:

| agent.yaml | Agent SDK option |
|---|---|
| `model`, `effort`, `max_turns`, `max_budget_usd` | same names |
| `system_prompt` + `system_prompt_mode` | `system_prompt` (string replaces Claude Code's prompt; `append` keeps it and appends) |
| `builtin_tools` | `tools` + `allowed_tools` |
| `mcp` | `mcp_servers`: in-process `warehouse` / `governance` tools, or dbt charts' own `dct` MCP server |
| `skills` | `skills` - copied from `agents/<x>/skills/` into the workspace's `.claude/skills/` |
| `tools.py` | extra in-process MCP tools (`build_tools(ws)` returning `@tool` functions) |
| `CLAUDE.md` | copied to the workspace root, loaded because `setting_sources=["project"]` |

`setting_sources=["project"]` means nothing from the machine running the benchmark
(your `~/.claude`) leaks into the agent: two people running the same agent directory get
the same context. WebFetch/WebSearch are disabled.

## Traces (`factory/tracing.py`)

`trace.jsonl` has one event per assistant text, tool call and tool result, plus `init`
and `result` (cost, turns, tokens, duration). `summary.json` aggregates it and the
benchmark adds `score` and `grades`. The line manager reads exactly these files.

Agno runs produce the same events and summary (`framework: agno`), with three differences: the
events are written when the run ends, so they all carry the end time; there is no `init` event;
and the cost is computed from the token counts with the price table in `factory/tracing.py`,
because Agno does not report a cost for Claude models.

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
