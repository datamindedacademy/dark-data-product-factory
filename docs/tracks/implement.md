# Track: Implementation agent

**Station.** Takes a spec and implements it as dbt models in
`warehouse/models/marts/<id>/`, with YAML docs, contracts and tests, then checks the
result against the spec's acceptance checks (`factory accept`). In the e2e line it also
handles rework from review and governance (`input/feedback.md`).

```bash
factory run implement --case implement-01-category
factory bench run implement --repeat 3
```

**Graded on** dbt build, outputs matching the spec, visible acceptance checks, **hidden**
acceptance checks (not in the agent's spec - do you generalise or just pass the tests?)
and the standards linter.

**Ideas to improve**
- Enable and improve `skills/dbt-duckdb` (contract data types are the classic time sink).
- Put the standards in context (skill or CLAUDE.md) or give the agent the `checkup` tool so
  governance does not bounce the product back.
- Make "done" explicit: build passes, acceptance passes, checkup clean.
- Reuse over re-derivation: point the agent at the core marts.
- Cost: does it need the biggest model? Try `claude-sonnet-5-5` with a good skill.
- Stretch: a planner subagent that writes the model design before any SQL.

**Benchmark ideas.** A spec that requires a spine (dates with no activity), one where the
grain is easy to get wrong, one with a rework round (feedback.md with review findings).
