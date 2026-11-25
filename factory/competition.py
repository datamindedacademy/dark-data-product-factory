"""The final challenge: build a submission from trusted code and score it against a hidden oracle.

Used by ``.github/workflows/competition.yml`` (see ``docs/competition.md``). Three jobs, three trust levels::

    run    (API key, runs team code)        factory e2e ... ; factory ci export-submission submission/
    build  (no secrets, runs untrusted SQL) factory ci check-cases ... ; factory ci build-submission submission/ build/
    grade  (hidden oracle, no team code)    factory ci score --oracle <spec.yaml> ...

Everything that crosses a job boundary is treated as untrusted *data*: ``build`` copies only SQL and
YAML out of the submission into a clean checkout, ``grade`` only reads JSON, YAML and a DuckDB file.

The oracle is a golden spec (``benchmark/products/*/spec.yaml`` are examples): its ``outputs`` are the
interface published in the issue, its acceptance checks are the hidden checks.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import duckdb
import yaml

from factory import paths, workspace
from factory.acceptance import missing_outputs, run_acceptance
from factory.contracts import DataProductSpec

# Points per component (sum = 100) and the efficiency scale: full marks at or below the first
# value, zero at or above the second. Calibrate the scale on a baseline run before the day.
# Correctness dominates: a well-governed, nicely charted product with wrong numbers is still wrong.
POINTS = {"correctness": 50, "interface": 5, "governance": 10, "dashboard": 10, "efficiency": 15, "benchmark": 10}
COST_USD = (0.03, 0.20)  # half and three times the Gemma baseline line ($0.05-0.06 a run, 2026-11-25)
DURATION_S = (600.0, 2700.0)  # TODO: recalibrate on a CI run of the baseline (the run job includes setup)
BENCHMARK_CASES = 3  # new, valid benchmark cases needed for full marks
_PRODUCT_FILES = {".sql", ".yml", ".yaml", ".md"}  # no .py: dbt Python models would be team code in the build job


def final_issue(issue: Path, oracle: Path) -> str:
    """The issue text plus the interface the product must expose - generated from the oracle so they cannot drift."""
    spec = DataProductSpec.load(oracle)
    lines = [issue.read_text().rstrip(), "", "## Interface (required)", "",
             "Other tools will read this product, so these names are fixed:", "",
             f"- Product id: `{spec.id}` (models in `warehouse/models/marts/{spec.id}/`, "
             f"dashboard in `warehouse/charts/{spec.id}.yml`)",
             "- The dashboard answers these questions; say which chart answers which (`Q1`, `Q2`, ...):"]
    lines += [f"  - **{q.id}** {q.question}" for q in spec.business_questions]
    for o in spec.outputs:
        lines += ["", f"### `{o.name}` - one row per {' × '.join(o.grain)}", "", o.description.strip(), "",
                  "| column | type | meaning |", "|---|---|---|"]
        lines += [f"| `{c.name}` | {c.data_type or ''} | {c.description.replace('|', '/')} |" for c in o.columns]
    return "\n".join(lines) + "\n"


def export_submission(dest: Path) -> Path | None:
    """Copy what the latest ``factory e2e`` run delivered (spec, models, board, traces) into ``dest``."""
    dest.mkdir(parents=True, exist_ok=True)
    summaries = sorted(paths.RUNS.glob("*/e2e_summary.json"))
    if not summaries:
        return None
    from factory.ci import collect_runs

    collect_runs(dest / "traces")
    shutil.copy(summaries[-1], dest / "e2e_summary.json")
    ws = summaries[-1].parent / "workspace"
    try:
        spec = DataProductSpec.load(ws / "output" / "spec.yaml")
    except Exception:  # noqa: BLE001 - no valid spec, nothing more to export
        return dest
    shutil.copy(ws / "output" / "spec.yaml", dest / "spec.yaml")
    if (models := ws / "warehouse" / "models" / "marts" / spec.id).is_dir():
        shutil.copytree(models, dest / "models", dirs_exist_ok=True)
    if (board := ws / "warehouse" / "charts" / f"{spec.id}.yml").exists():
        shutil.copy(board, dest / "board.yml")
    return dest


def valid_case(path: Path) -> tuple[bool, str]:
    """A benchmark case is valid when doing nothing scores 0 and the oracle scores 1 (what ``pytest`` checks)."""
    from benchmark.core import Case, weighted
    from benchmark.harness import STAGES

    try:
        case = Case.load(path)
        stage = STAGES[case.stage]
        ws = workspace.create(paths.RUNS / workspace.new_run_id(f"case-{case.id}"))
        stage.setup(case, ws)
        nothing = weighted(stage.grade(case, ws))
        stage.oracle(case, ws)
        golden = weighted(stage.grade(case, ws))
    except Exception as exc:  # noqa: BLE001 - a broken case is an invalid case
        return False, f"{type(exc).__name__}: {str(exc)[:200]}"
    return nothing == 0 and golden >= 0.99, f"nothing={nothing:.2f} oracle={golden:.2f}"


def build_submission(submission: Path, out: Path) -> dict[str, Any]:
    """Build the submitted product in a clean workspace; write ``warehouse.duckdb`` and ``build.json`` to ``out``."""
    from factory.tools import checkup

    out.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"models": 0, "dbt_build": False, "checkup_violations": None, "dct_validate": False,
                              "dct_render": False}
    try:
        spec = DataProductSpec.load(submission / "spec.yaml")
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"no valid spec.yaml in the submission: {str(exc)[:300]}"
    else:
        ws = workspace.create(paths.RUNS / workspace.new_run_id("submission"))
        target = ws / "warehouse" / "models" / "marts" / spec.id
        for f in sorted((submission / "models").rglob("*")):
            if f.is_file() and not f.is_symlink() and f.suffix in _PRODUCT_FILES:
                (target / f.relative_to(submission / "models")).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(f, target / f.relative_to(submission / "models"))
                result["models"] += f.suffix == ".sql"
        rel = f"charts/{spec.id}.yml"
        if (submission / "board.yml").is_file():
            shutil.copy(submission / "board.yml", ws / "warehouse" / rel)
        build = workspace.dbt(ws, "build")
        result["dbt_build"] = build.returncode == 0
        result["dbt_tail"] = (build.stdout or "").strip()[-1500:]
        if workspace.dbt(ws, "parse", "--quiet").returncode == 0:
            result["checkup_violations"] = checkup.run(ws / "warehouse", spec.id,
                                                       checkup.MECHANICAL_RULES + checkup.JUDGEMENT_RULES)["violations"]
        if (ws / "warehouse" / rel).exists():
            result["dct_validate"] = workspace.dct(ws, "validate", rel).returncode == 0
            result["dct_render"] = workspace.dct(ws, "render", rel, "--format", "text-data", "--no-cache",
                                                 "--no-warnings").returncode == 0
            workspace.dct(ws, "render", rel, "--format", "html", "--output", str((out / "dashboard.html").resolve()))
        shutil.copy(ws / "warehouse" / "warehouse.duckdb", out / "warehouse.duckdb")
    (out / "build.json").write_text(json.dumps(result, indent=2, default=str))
    return result


def _scale(x: float | None, lo_hi: tuple[float, float]) -> float:
    lo, hi = lo_hi
    return 0.0 if x is None else max(0.0, min(1.0, (hi - x) / (hi - lo)))


def score(submission: Path, build: Path, oracle: Path, pristine_db: Path, duration_s: float | None = None,
          cost_usd: float | None = None) -> dict[str, Any]:
    """Score one team. Runs no team code: reads YAML/JSON and queries the built DuckDB file read-only."""
    from benchmark.stages.bi import answered_questions

    spec = DataProductSpec.load(oracle)
    b = json.loads((build / "build.json").read_text()) if (build / "build.json").exists() else {}
    part = dict.fromkeys(POINTS, 0.0)
    detail = dict.fromkeys(POINTS, "nothing to grade")

    try:
        board = yaml.safe_load((submission / "board.yml").read_text()) or {}
        board = board if isinstance(board, dict) else {}
    except (OSError, yaml.YAMLError):
        board = {}
    passed_q: set[str] = set()  # questions whose hidden checks all pass

    db = build / "warehouse.duckdb"
    if db.exists():  # also when `dbt build` failed: whatever did build is graded, a missing model fails its checks
        hidden = run_acceptance(spec, db, ref_db=pristine_db)
        part["correctness"] = hidden.score
        detail["correctness"] = f"{hidden.passed}/{hidden.total} hidden checks: " + ", ".join(
            f"{r.id} {'pass' if r.passed else 'FAIL'}" for r in hidden.results)
        ok = {r.id for r in hidden.results if r.passed}
        passed_q = {q.id for q in spec.business_questions if q.acceptance and all(c.id in ok for c in q.acceptance)}
        con = duckdb.connect(str(db), read_only=True, config={"enable_external_access": False})
        try:
            missing, n = missing_outputs(spec, con)
        finally:
            con.close()
        part["interface"] = 1 - len(missing) / max(n, 1)
        detail["interface"] = f"missing {missing}" if missing else "every required model and column exists"
    elif b.get("error"):
        detail["correctness"] = detail["interface"] = b["error"]

    viol = b.get("checkup_violations")
    if b.get("dbt_build") and b.get("models") and viol is not None:
        part["governance"] = max(0.0, 1 - len(viol) / 5)
        detail["governance"] = f"{len(viol)} checkup violations " + \
            ", ".join(sorted({v["rule_id"] for v in viol}))
    elif b.get("models"):
        detail["governance"] = "dbt build failed (models or tests)"

    # A question counts as answered only when a placed chart names it AND its hidden checks pass:
    # a chart of a wrong number does not answer the question.
    wanted = {q.id for q in spec.business_questions}
    right = wanted & answered_questions(board) & passed_q
    part["dashboard"] = (bool(b.get("dct_validate")) + bool(b.get("dct_render")) + len(right) / len(wanted)) / 3
    detail["dashboard"] = (f"validate {'ok' if b.get('dct_validate') else 'failed'}, render "
                           f"{'ok' if b.get('dct_render') else 'failed'}, answered correctly {sorted(right)} of {sorted(wanted)}")

    # In the final, cost_usd is the spend of the team's final-only OpenRouter key, read by the grade job
    # (key_usage): measured, outside the team's reach, like the duration. Without it (practice runs) the cost
    # comes from the traces, which team code wrote: self-reported. A missing cost counts as the worst cost.
    runs = [json.loads(p.read_text()) for p in sorted((submission / "traces").rglob("summary.json"))]
    costs = [r.get("total_cost_usd") for r in runs]
    reported = sum(costs) if runs and all(c is not None for c in costs) else None
    cost = cost_usd if cost_usd is not None else reported
    part["efficiency"] = part["correctness"] * (_scale(cost, COST_USD) + _scale(duration_s, DURATION_S)) / 2
    detail["efficiency"] = (f"${cost:.2f}" if cost is not None else "cost not reported") + \
        (" (measured on the key)" if cost_usd is not None else " (from the traces)") + \
        (f", {duration_s / 60:.0f} min" if duration_s is not None else ", duration unknown") + \
        f", scaled by correctness; {len(runs)} agent runs"

    cases = json.loads((build / "cases.json").read_text()) if (build / "cases.json").exists() else {}
    ok = sum(1 for v in cases.values() if v[0])
    part["benchmark"] = min(ok, BENCHMARK_CASES) / BENCHMARK_CASES
    detail["benchmark"] = f"{ok} of {len(cases)} new cases valid (need {BENCHMARK_CASES})"

    points = {k: round(POINTS[k] * part[k], 1) for k in POINTS}
    return {"total": round(sum(points.values()), 1), "points": points, "max": POINTS, "detail": detail,
            "cost_usd": cost, "reported_cost_usd": reported, "duration_s": duration_s,
            "agno_stations": sorted({r.get("stage") or r.get("agent") for r in runs if r.get("framework") == "agno"})}


def score_markdown(team: str, s: dict[str, Any]) -> str:
    lines = [f"### 🏁 Final challenge: `{team}` scores {s['total']:g} / 100", "", "| component | points | detail |", "|---|---:|---|"]
    lines += [f"| {k} | {s['points'][k]:g} / {s['max'][k]} | {s['detail'][k].replace('|', '/')} |" for k in s["max"]]
    lines += ["", "Stations built with Agno: " + (", ".join(s["agno_stations"]) or "**none**")]
    return "\n".join(lines) + "\n"


def key_usage(key: str, settle_s: float = 5, tries: int = 12) -> float:
    """What an OpenRouter key has spent so far, in USD. Waits until two reads agree: usage can lag a few seconds."""
    import time
    import urllib.request

    def read() -> float:
        req = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return float(json.load(r)["data"]["usage"])

    last = read()
    for _ in range(tries):
        time.sleep(settle_s)
        now = read()
        if now == last:
            return now
        last = now
    return last
