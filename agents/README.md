# Agents

One directory per station. **Copy the baseline before you change it** so you can
compare variants on the benchmark:

```bash
cp -r agents/intake agents/intake-ourteam
# edit agents/intake-ourteam/...
factory bench run intake --agent-dir agents/intake-ourteam --label ourteam-v1 --repeat 3
factory bench report --stage intake
```

## Anatomy

```
agents/<station>/
  agent.yaml          model, effort, budgets, built-in tools, MCP servers, skills, expected outputs
  system_prompt.md    role and working method ($workspace is substituted)
  prompt.md           the task message ($product_id, $workspace, $repo_root are substituted)
  skills/<name>/SKILL.md   skills; only those listed in agent.yaml `skills:` are installed
  tools.py            optional: def build_tools(ws: Path) -> list of @tool functions (in-process MCP)
  CLAUDE.md           optional: repo-level context placed at the workspace root
```

`agent.yaml` reference:

```yaml
model: default                 # FACTORY_MODEL or claude-opus-5-5; e.g. claude-sonnet-5-5, claude-haiku-5-5
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
6. **Model and effort.** A smaller model with a better skill can beat a bigger model
   without one, at a fraction of the cost. Measure both axes.
7. **Structure.** Split the job: subagents (`agents=` in the SDK), a planner and an
   executor, or a deterministic pre-step in `tools.py`.

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
