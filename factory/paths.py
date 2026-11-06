from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "warehouse"
WAREHOUSE_DB = WAREHOUSE / "warehouse.duckdb"
AGENTS = ROOT / "agents"
BENCHMARK = ROOT / "benchmark"
PRODUCTS = BENCHMARK / "products"
CASES = BENCHMARK / "cases"
RESULTS = BENCHMARK / "results"
STANDARDS = ROOT / "standards"
RUNS = Path(os.environ.get("FACTORY_RUNS_DIR", ROOT / "runs"))
BIN = Path(os.environ.get("FACTORY_BIN", ROOT / ".venv" / "bin"))


def tool(name: str) -> str:
    """Path to a CLI installed in the project venv (dbt, dct), falling back to PATH."""
    p = BIN / name
    return str(p) if p.exists() else name
