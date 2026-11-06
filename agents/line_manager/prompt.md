`input/runs/` contains the runs of the last week. Each run directory has:
- `summary.json`: agent, case, status, cost, turns, duration, tool call counts, score (0-1)
- `trace.jsonl`: every tool call and tool result of the run

The agents' current configuration is in `agents/` (agent.yaml, prompts, skills).

Find the recurring problems that cost the most (money, time or quality) and recommend
concrete changes. Write `output/recommendations.json`:

```json
{
  "summary": "...",
  "recommendations": [
    {"target_agent": "intake|implement|review|governance|bi|factory",
     "pattern": "what keeps happening", "evidence": "run ids, counts, cost",
     "impact": "what it costs us", "change": "the concrete change", "file": "agents/x/..."}
  ]
}
```

Also write a short human-readable report to `output/report.md`.
Validate with `factory validate line_manager output/recommendations.json`.
