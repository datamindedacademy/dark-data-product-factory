# Line manager

Reads the traces of many runs and recommends changes to the other agents. Not part of the final.

**In** `input/runs/` **Out** `output/recommendations.json`, `output/report.md`

**Try**
- DuckDB on the traces (`read_json_auto('input/runs/*/trace.jsonl')`) instead of reading them
