# Agents

One folder per station; each has a short README. `agents/<station>/` is the line the final runs.
`agents/line.yaml` sets how many rework rounds the line allows.

## How to work

Start with **one agent**, the one where the most points are. Work in a copy so you can compare:

```bash
cp -r agents/intake agents/intake-ourteam
```

1. **Benchmark.** Add a case of your own in `benchmark/cases/<station>/`, then run:
   `factory bench run intake --agent-dir agents/intake-ourteam --label v1 --repeat 3`
2. **Traces.** Read `runs/bench-<time>-intake-v1/<case>-r<n>/trace.jsonl` of the cases that lost points: what went wrong?
3. **Context.** Change one thing: prompt, skill, tool or MCP server.
4. **Repeat.** Run the benchmark again (`--label v2`) and compare with `factory bench report`. Keep it or revert it.

When the agent stops improving, promote it and take the next agent:

```bash
rm -rf agents/intake && cp -r agents/intake-ourteam agents/intake
```

## Agno agents

Every agent is an [Agno](https://docs.agno.com) agent. Without an `agent.py`, the runner builds it
from `agent.yaml` (below), so a first change is often a prompt, a skill or a tool in the yaml.
For full control add an `agent.py`; `agents/intake-agno/` is an example:

```python
def build_agent(ws: Path, cfg) -> Agent:     # ws: the run's workspace, cfg: this directory's agent.yaml
    return Agent(model=llm.model(cfg.model), instructions=..., tools=[run_sql, FileTools(base_dir=ws)])  # from factory import llm
```

The runner renders `prompt.md`, calls `await build_agent(ws, cfg).arun(prompt)` and writes
`trace.jsonl` and `summary.json`. Every agent gets a hook that refuses calls outside the workspace.

- **Skills:** `skills=Skills(loaders=[LocalSkills(str(cfg.dir / "skills"))])` (`from agno.skills
  import Skills, LocalSkills`). Each skill is a folder with a `SKILL.md` that starts with `name`
  and `description` front matter, like `agents/implement/skills/dbt-duckdb`.
- **An existing MCP server:** add `MCPTools(command=f"dct mcp serve --project-dir {ws / 'warehouse'}")`
  (`from agno.tools.mcp import MCPTools`) to `tools`. Agno connects and disconnects it per run.
- **Your own MCP server:** a `server.py` next to `agent.py` built with
  `mcp.server.fastmcp.FastMCP`, connected with `MCPTools(command=f"python {cfg.dir / 'server.py'} {ws}")`.
- **The shell:** `from factory.runner import bash_tool` gives the same `bash` tool as the
  baselines; `dbt`, `dct`, `checkup` and `factory` are on its `PATH`.
- **Cost** in the summary is what OpenRouter reports for the run, for any model.

Python packages are those in `pyproject.toml`: the final challenge installs the organisers' lock
file, not yours.

## Anatomy

```
agents/<station>/
  README.md           what the agent is responsible for, its input and output, tools and hints
  agent.yaml          model, effort, turn limit, built-in tools, MCP servers, skills, expected outputs
  system_prompt.md    role and working method ($workspace is substituted)
  prompt.md           the task message ($product_id, $workspace, $repo_root are substituted)
  skills/<name>/SKILL.md   skills; only those listed in agent.yaml `skills:` are loaded
  tools.py            optional: def build_tools(ws: Path) -> list of functions, added as tools
  agent.py            optional: def build_agent(ws, cfg) -> agno.agent.Agent (agent.yaml's tools are then ignored)
  CLAUDE.md           optional: repo context, appended to the instructions
```

`agent.yaml` reference:

```yaml
model: default                 # FACTORY_MODEL or google/gemma-4-31b-it; any OpenRouter model id, e.g. qwen/qwen3.5-397b-a17b
effort: medium                 # optional, for reasoning models: low | medium | high
max_turns: 60                  # tool calls per run
system_prompt: system_prompt.md
prompt: prompt.md
builtin_tools: [Read, Write, Edit, Glob, Grep, Bash]   # file tools in the workspace + a bash tool
mcp:
  warehouse: [run_sql]         # + list_tables, describe_table
  governance: [checkup]        # runs `checkup run` (warehouse/checkup.yaml)
  dct: true                    # dbt charts' own MCP server
skills: [dbt-duckdb]
outputs: [output/spec.yaml]    # recorded as missing_outputs in the summary if absent
```

## Levers, roughly from cheapest to most effort

1. **Prompt.** State the working method (investigate before writing, verify before
   finishing), the definition of done, and what to do when blocked.
2. **Verification loops.** Tell the agent which command proves it is done
   (`factory accept`, `dct validate`, `factory validate`). Agents that check their work
   score higher.
3. **Skills.** Durable know-how loaded on demand: DuckDB/dbt gotchas, Fernhill's
   business rules, how to write acceptance checks, dbt charts syntax (`dct skills chart`
   prints the official one; `agents/implement/skills/dbt-duckdb` is an example, disabled
   in the baseline).
4. **CLAUDE.md.** Always-on repo context: layout, conventions, where the traps are.
   Skills vs. CLAUDE.md is a context-budget trade-off - measure it.
5. **Tools / MCP.** Better data access (`describe_table`, a catalogue built from the dbt
   manifest, a semantic layer of metric definitions), the `dct` MCP server, or a tool that
   does a deterministic part of the job so the model does not have to.
   A semantic layer in [Apache Ossie](https://ossie.apache.org/) format (the vendor-neutral
   metrics standard, formerly Open Semantic Interchange) is the strongest version of this:
   write Fernhill's metrics once ("net revenue excludes cancelled orders and QA accounts,
   in EUR") and every station reads the same definitions, as a skill or through an MCP tool.
6. **Model and effort.** A smaller model with a better skill can beat a bigger model
   without one, at a fraction of the cost. Measure both axes.
7. **Structure.** Split the job: a team of agents (Agno `Team`), a
   planner and an executor, or a deterministic step in a tool.

## Known weak spots of the baselines

Hypotheses, not measurements - check them in the traces of your first runs.

| Station | Likely weaknesses |
|---|---|
| intake | explores the schema query by query; does not know Fernhill's business rules (QA accounts, cancellations, GBP); writes vague acceptance checks; rarely says "this cannot be built" |
| implement | contract `data_type` mismatches (DuckDB `hugeint`, `date_trunc` returns timestamp); does not read the standards; stops after `dbt build` without running acceptance |
| review | reads whole files instead of the diff; does not run the numbers (`factory accept`); approves when the PR description sounds confident |
| governance | trusts `checkup` and misses the judgement rules (GOV-006, 008, 010, 011) |
| bi | dbt charts syntax errors (e.g. `title` on KPIs); averages ratios; forgets the `notes` that tie queries to questions |
| line manager | reads traces one by one and runs out of context; recommendations without numbers |
