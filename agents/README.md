# Agents

One directory per station. `agents/<station>/` is the line: what `factory e2e`, the CI
pipelines and the final challenge run. **Work in a copy** so you can compare variants on the
benchmark, and promote the winner by copying it over `agents/<station>/`:

```bash
cp -r agents/intake-agno agents/intake-ourteam
# edit agents/intake-ourteam/...
factory bench run intake --agent-dir agents/intake-ourteam --label ourteam-v1 --repeat 3
factory bench report --stage intake
rm -rf agents/intake && cp -r agents/intake-ourteam agents/intake     # promote (the baseline stays in git)
```

## Agno agents

Add an `agent.py` to an agent directory and the factory runs it with [Agno](https://docs.agno.com)
instead of the Claude Agent SDK. `agents/intake-agno/` is the starter:

```python
def build_agent(ws: Path, cfg) -> Agent:     # ws: the run's workspace, cfg: this directory's agent.yaml
    return Agent(model=Claude(id=cfg.model), instructions=..., tools=[run_sql, FileTools(base_dir=ws), ShellTools(base_dir=ws)])
```

The runner renders `prompt.md`, calls `await build_agent(ws, cfg).arun(prompt)` and writes the
same `trace.jsonl` and `summary.json` as for a baseline. From `agent.yaml` it uses `model`,
`prompt`, `skills` and `outputs`; tools, skills and MCP servers are what you give the `Agent`:

- **Another station:** copy the starter, point `system_prompt` and `prompt` in `agent.yaml` at
  that station's files (or your own copies) and set its `outputs`. Agents that build or check
  things need the shell: `dbt`, `dct`, `checkup` and `factory` are on its `PATH`.
- **Skills:** `skills=Skills(loaders=[LocalSkills(str(cfg.dir / "skills"))])` (`from agno.skills
  import Skills, LocalSkills`). Each skill is a folder with a `SKILL.md` that starts with `name`
  and `description` front matter, like `agents/implement/skills/dbt-duckdb`.
- **An existing MCP server:** add `MCPTools(command=f"dct mcp serve --project-dir {ws / 'warehouse'}")`
  (`from agno.tools.mcp import MCPTools`) to `tools`. Agno connects and disconnects it per run.
- **Your own MCP server:** a `server.py` next to `agent.py` built with
  `mcp.server.fastmcp.FastMCP`, connected with `MCPTools(command=f"python {cfg.dir / 'server.py'} {ws}")`.
- **Budget:** `max_budget_usd` is not enforced for Agno agents. The starter passes `max_turns` as
  `tool_call_limit`. Effort: `Claude(id=cfg.model, output_config={"effort": cfg.effort})`.
- **Cost** in the summary is computed from token counts for the models in `factory/tracing.py`.
  Other models report no cost, which the final challenge scores as the worst cost.

Python packages are those in `pyproject.toml`: the final challenge installs the organisers' lock
file, not yours.

## Anatomy

```
agents/<station>/
  agent.yaml          model, effort, budgets, built-in tools, MCP servers, skills, expected outputs
  system_prompt.md    role and working method ($workspace is substituted)
  prompt.md           the task message ($product_id, $workspace, $repo_root are substituted)
  skills/<name>/SKILL.md   skills; only those listed in agent.yaml `skills:` are installed
  tools.py            optional, Agent SDK agents: def build_tools(ws: Path) -> list of @tool functions (in-process MCP)
  agent.py            optional: def build_agent(ws, cfg) -> agno.agent.Agent - makes it an Agno agent (see above)
  CLAUDE.md           optional: repo-level context placed at the workspace root
```

`agent.yaml` reference (`effort` to `mcp` apply to Agent SDK agents only):

```yaml
model: default                 # FACTORY_MODEL or claude-haiku-5-5; e.g. claude-sonnet-5-5, claude-opus-5-5
effort: medium                 # low | medium | high | xhigh | max
max_turns: 60
max_budget_usd: 3.0            # hard stop per run
system_prompt: system_prompt.md
system_prompt_mode: replace    # replace = only your prompt; append = Claude Code's prompt + yours
prompt: prompt.md
builtin_tools: [Read, Write, Edit, Glob, Grep, Bash]
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
7. **Structure.** Split the job: a team of agents (Agno `Team`, `agents=` in the Agent SDK), a
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
