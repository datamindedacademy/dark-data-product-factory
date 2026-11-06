"""Generate a week of synthetic factory runs with planted, recurring problems.

The line-manager benchmark needs traces with *known* bottlenecks so it can be
graded. Real traces from your own benchmark runs (runs/**/trace.jsonl) have the
same format - once your team has produced some, try the line manager on those too.

Planted patterns (the answer key lives in benchmark/cases/line_manager/*.yaml):

* implement: dbt contract errors on data types (hugeint vs bigint, timestamp vs
  date) make the agent rebuild 3-6 times per run.
* intake: the agent explores the schema one table at a time with
  information_schema / DESCRIBE queries - ~40% of its tool calls.
* review: the agent Reads dozens of unchanged files instead of looking at the
  diff - it is the most expensive agent per run.
* bi: `dct validate` keeps failing on KPI charts that use `title:` (KPIs take
  `label:`) and on unknown keys.
* governance rejects most implementations for missing meta.owner / column
  descriptions (GOV-005, GOV-003): rework that should be prevented upstream.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

PRODUCTS = ["category_performance", "marketing_performance", "customer_retention", "store_performance",
            "supplier_lead_times", "basket_analysis", "loyalty_tiers", "stock_cover"]
TABLES = ["raw.orders", "raw.order_items", "raw.products", "raw.customers", "raw.returns", "raw.web_sessions",
          "raw.marketing_spend", "raw.stores", "raw.fx_rates", "main.fct_orders", "main.fct_order_items",
          "main.dim_customers", "main.dim_products", "main.stg_returns"]


class Run:
    def __init__(self, rng: random.Random, agent: str, case: str, start: datetime):
        self.rng, self.agent, self.case, self.start = rng, agent, case, start
        self.events: list[dict] = []
        self.t = 0.0
        self.turn = 0
        self.n = 0
        self.tool_calls: dict[str, int] = {}
        self.tool_errors: dict[str, int] = {}
        self.input_tokens = 0
        self.output_tokens = 0

    def _ev(self, **kw) -> None:
        self.t += self.rng.uniform(1.5, 9)
        self.events.append({"t": round(self.t, 2), **kw})

    def say(self, text: str) -> None:
        self.turn += 1
        self.output_tokens += len(text) // 3 + 200
        self._ev(type="assistant_text", turn=self.turn, chars=len(text), text=text)

    def tool(self, name: str, inp: dict, result: str, is_error: bool = False, result_tokens: int | None = None) -> None:
        self.turn += 1
        self.n += 1
        tid = f"toolu_{self.n:04d}"
        self.tool_calls[name] = self.tool_calls.get(name, 0) + 1
        if is_error:
            self.tool_errors[name] = self.tool_errors.get(name, 0) + 1
        self.output_tokens += 150 + len(json.dumps(inp)) // 3
        self.input_tokens += result_tokens or len(result) // 3
        self._ev(type="tool_use", turn=self.turn, id=tid, name=name, input=inp)
        self._ev(type="tool_result", turn=self.turn, id=tid, name=name, is_error=is_error,
                 chars=len(result), preview=result[:600])

    def finish(self, out: Path, score: float, status: str = "ok") -> None:
        # Context grows every turn: input tokens are re-read each turn (with caching ~10%).
        base_ctx = 9000 + self.input_tokens
        total_in = int(base_ctx * self.turn * 0.55)
        cache_read = int(total_in * 0.8)
        cost = (total_in - cache_read) * 4e-6 + cache_read * 0.2e-6 + self.output_tokens * 20e-6
        duration = int(self.t * 1000)
        self.events.insert(0, {"t": 0.0, "type": "init", "model": "claude-opus-5-5", "tools": [], "skills": []})
        self.events.append({"t": round(self.t + 1, 2), "type": "result", "subtype": "success", "is_error": False,
                            "num_turns": self.turn, "duration_ms": duration, "total_cost_usd": round(cost, 4),
                            "usage": {"input_tokens": total_in - cache_read, "cache_read_input_tokens": cache_read,
                                      "output_tokens": self.output_tokens}})
        run_id = f"{self.start:%Y%m%d-%H%M%S}-{self.agent}-{self.rng.randrange(16**6):06x}"
        d = out / run_id
        d.mkdir(parents=True)
        with (d / "trace.jsonl").open("w") as f:
            for e in self.events:
                f.write(json.dumps(e) + "\n")
        summary = {"run_id": run_id, "agent": self.agent, "case": self.case, "started_at": self.start.isoformat(),
                   "model": "claude-opus-5-5", "status": status, "num_turns": self.turn, "duration_ms": duration,
                   "total_cost_usd": round(cost, 4), "input_tokens": total_in - cache_read,
                   "cache_read_input_tokens": cache_read, "output_tokens": self.output_tokens,
                   "tool_calls": self.tool_calls, "tool_errors": self.tool_errors, "score": round(score, 2)}
        (d / "summary.json").write_text(json.dumps(summary, indent=2))


def intake_run(rng, out, start, product):
    r = Run(rng, "intake", f"intake-{product}", start)
    r.tool("Read", {"file_path": "input/issue.md"}, "---\ntitle: ...\n---\n## What do you need? ...")
    r.say("I'll start by exploring the warehouse schema.")
    r.tool("mcp__warehouse__run_sql", {"sql": "select table_schema, table_name from information_schema.tables"},
           "table_schema | table_name\n--- | ---\nraw | orders\nraw | order_items\n...")
    for t in rng.sample(TABLES, rng.randint(9, 14)):
        r.tool("mcp__warehouse__run_sql", {"sql": f"describe {t}"}, "column_name | column_type | null\n--- | --- | ---\n...")
        r.tool("mcp__warehouse__run_sql", {"sql": f"select * from {t} limit 5"}, "... 5 rows ...", result_tokens=900)
        if rng.random() < 0.5:
            col = rng.choice(["status", "currency", "category", "channel", "traffic_source"])
            r.tool("mcp__warehouse__run_sql", {"sql": f"select {col}, count(*) from {t} group by 1"},
                   f"Binder Error: Referenced column \"{col}\" not found" if rng.random() < 0.4 else f"{col} | count\n...",
                   is_error=False)
    r.say("Now I understand the data. Let me check the business rules.")
    for _ in range(rng.randint(3, 6)):
        r.tool("mcp__warehouse__run_sql", {"sql": "select count(*) from main.fct_orders where ..."}, "count\n---\n14301")
    r.tool("Write", {"file_path": "output/spec.yaml", "content": "spec_version: 1\n..."}, "File created")
    r.tool("Bash", {"command": "factory validate spec output/spec.yaml"}, "OK: output/spec.yaml is a valid spec")
    r.say("The spec is written.")
    r.finish(out, rng.uniform(0.62, 0.86))


CONTRACT_ERRORS = [
    "Compilation Error in model fct_{p}\n  This model has an enforced contract that failed.\n  | column_name | definition_type | contract_type | mismatch_reason |\n  | units_sold  | HUGEINT         | BIGINT        | data type mismatch |",
    "Compilation Error in model fct_{p}\n  This model has an enforced contract that failed.\n  | month | TIMESTAMP | DATE | data type mismatch |",
    "Compilation Error in model fct_{p}\n  This model has an enforced contract that failed.\n  | orders | BIGINT | INTEGER | data type mismatch |",
]


def implement_run(rng, out, start, product, contract_trouble: bool, missing_meta: bool):
    r = Run(rng, "implement", f"implement-{product}", start)
    r.tool("Read", {"file_path": "input/spec.yaml"}, "spec_version: 1\nid: " + product)
    r.tool("Glob", {"pattern": "warehouse/models/**/*.sql"}, "warehouse/models/marts/core/fct_orders.sql\n...")
    r.tool("Read", {"file_path": "warehouse/models/marts/core/fct_orders.sql"}, "with orders as (...)")
    r.tool("Write", {"file_path": f"warehouse/models/marts/{product}/fct_{product}.sql"}, "File created")
    yml = "models:\n  - name: fct_" + product + ("\n    config: {contract: {enforced: true}}" if missing_meta else "\n    config: {contract: {enforced: true}, meta: {owner: analytics-engineering}}")
    r.tool("Write", {"file_path": f"warehouse/models/marts/{product}/_{product}.yml", "content": yml}, "File created")
    attempts = rng.randint(3, 6) if contract_trouble else rng.choice([1, 1, 2])
    for i in range(attempts):
        ok = i == attempts - 1
        if ok:
            r.tool("Bash", {"command": f"cd warehouse && dbt build --select fct_{product}"},
                   "Done. PASS=6 WARN=0 ERROR=0 SKIP=0 TOTAL=6")
        else:
            err = rng.choice(CONTRACT_ERRORS).format(p=product) if contract_trouble else "Runtime Error: Binder Error: column not found"
            r.tool("Bash", {"command": f"cd warehouse && dbt build --select fct_{product}"},
                   err + "\nDone. PASS=0 WARN=0 ERROR=1 SKIP=5 TOTAL=6", is_error=True)
            r.say("The contract failed on a data type. Let me fix the type in the YAML and try again.")
            r.tool("Edit", {"file_path": f"warehouse/models/marts/{product}/_{product}.yml",
                            "old_string": "data_type: bigint", "new_string": "data_type: hugeint"}, "File edited")
    r.tool("Bash", {"command": "factory accept input/spec.yaml --db warehouse/warehouse.duckdb"},
           "5/6 acceptance checks passed" if rng.random() < 0.5 else "6/6 acceptance checks passed")
    r.say("Implemented the data product.")
    r.finish(out, rng.uniform(0.55, 0.8) if contract_trouble else rng.uniform(0.75, 0.95))


def review_run(rng, out, start, product):
    r = Run(rng, "review", f"review-{product}", start)
    r.tool("Read", {"file_path": "input/pr.md"}, "Adds data product ...")
    r.tool("Bash", {"command": "git log --oneline"}, "a1b2c3 Add data product\n9f8e7d base project")
    r.tool("Glob", {"pattern": "**/*"}, "\n".join(f"warehouse/models/{x}" for x in range(60)))
    files = ["warehouse/models/staging/" + f for f in ["stg_orders.sql", "stg_order_items.sql", "stg_products.sql",
             "stg_customers.sql", "stg_returns.sql", "stg_web_sessions.sql", "_sources.yml", "_staging.yml"]]
    files += ["warehouse/models/marts/core/" + f for f in ["fct_orders.sql", "fct_order_items.sql", "dim_customers.sql",
              "dim_products.sql", "_core.yml"]]
    files += ["warehouse/dbt_project.yml", "warehouse/profiles.yml", "standards/data-product-standards.md",
              "warehouse/charts/sales_overview.yml", "warehouse/macros/generate_schema_name.sql"]
    for f in files + rng.sample(files, rng.randint(4, 10)):
        r.tool("Read", {"file_path": f}, "...file content...", result_tokens=rng.randint(1500, 4000))
    r.tool("Read", {"file_path": f"warehouse/models/marts/{product}/fct_{product}.sql"}, "...", result_tokens=1200)
    r.tool("Bash", {"command": "cd warehouse && dbt build"}, "Done. PASS=44 WARN=0 ERROR=0", result_tokens=6000)
    r.tool("Write", {"file_path": "output/review.json"}, "File created")
    r.say("Review written.")
    r.finish(out, rng.uniform(0.6, 0.9))


def bi_run(rng, out, start, product):
    r = Run(rng, "bi", f"bi-{product}", start)
    r.tool("Read", {"file_path": "input/spec.yaml"}, "...")
    r.tool("mcp__warehouse__run_sql", {"sql": f"describe main.fct_{product}"}, "...")
    r.tool("Write", {"file_path": f"warehouse/charts/{product}.yml"}, "File created")
    errs = [
        "error[ERR-META-SCHEMA]: Board fragment schema error: charts.total_kpi.@inline.kpi: Value error, `title:` is not used on `type: kpi`. Use `label:` instead.\n  At: charts/{p}.yml",
        "error[ERR-META-SCHEMA]: Board fragment schema error: charts.trend: Extra inputs are not permitted: `subtitle`\n  At: charts/{p}.yml",
        "error[ERR-META-SCHEMA]: Board fragment schema error: charts.mix: chart-root `format:` is rejected; use the family slot (axis_y.labels.format)\n  At: charts/{p}.yml",
    ]
    for _ in range(rng.randint(2, 5)):
        r.tool("Bash", {"command": f"cd warehouse && dct validate charts/{product}.yml"},
               rng.choice(errs).format(p=product), is_error=True)
        r.tool("Edit", {"file_path": f"warehouse/charts/{product}.yml"}, "File edited")
    r.tool("Bash", {"command": f"cd warehouse && dct validate charts/{product}.yml"}, f"✓ charts/{product}.yml OK")
    r.tool("Bash", {"command": f"cd warehouse && dct render charts/{product}.yml --format text"}, "# Board\n## ...")
    r.say("Dashboard done.")
    r.finish(out, rng.uniform(0.6, 0.85))


def governance_run(rng, out, start, product, rejects: bool):
    r = Run(rng, "governance", f"governance-{product}", start)
    r.tool("Read", {"file_path": "standards/data-product-standards.md"}, "# Fernhill data product standards ...")
    if rejects:
        viol = [{"rule_id": "GOV-005", "model": f"fct_{product}", "column": None, "message": "meta.owner is missing"}]
        viol += [{"rule_id": "GOV-003", "model": f"fct_{product}", "column": c, "message": "column has no description"}
                 for c in rng.sample(["orders", "units", "net_revenue_eur", "month", "channel"], 3)]
    else:
        viol = []
    r.tool("mcp__governance__checkup", {"product": product}, json.dumps({"violations": viol})[:600])
    r.tool("Write", {"file_path": "output/governance.json"}, "File created")
    r.say("Not compliant: sending back to implementation." if rejects else "Compliant.")
    r.finish(out, rng.uniform(0.8, 1.0), status="ok")


def main(out: Path, seed: int = 7) -> None:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 10, 26, 8, 0)
    for day in range(5):
        for product in rng.sample(PRODUCTS, 3):
            t = start + timedelta(days=day, hours=rng.randint(0, 8), minutes=rng.randint(0, 59))
            intake_run(rng, out, t, product)
            missing_meta = rng.random() < 0.6
            implement_run(rng, out, t + timedelta(minutes=20), product, contract_trouble=rng.random() < 0.7,
                          missing_meta=missing_meta)
            review_run(rng, out, t + timedelta(minutes=45), product)
            governance_run(rng, out, t + timedelta(minutes=60), product, rejects=missing_meta)
            if missing_meta:  # rework loop: implement again, then governance again
                implement_run(rng, out, t + timedelta(minutes=70), product, contract_trouble=False, missing_meta=False)
                governance_run(rng, out, t + timedelta(minutes=90), product, rejects=False)
            bi_run(rng, out, t + timedelta(minutes=100), product)


if __name__ == "__main__":
    import sys

    main(Path(sys.argv[1] if len(sys.argv) > 1 else "runs/synthetic-week"))
