from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw"
AGENTS = ROOT / "agents"
BENCHMARK = ROOT / "benchmark"
PRODUCTS = BENCHMARK / "products"
CASES = BENCHMARK / "cases"
RESULTS = BENCHMARK / "results"
RUNS = Path(os.environ.get("FACTORY_RUNS_DIR", ROOT / "runs"))
