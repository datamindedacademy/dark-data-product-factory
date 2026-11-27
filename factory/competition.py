"""The final: score a team's answers against the hidden right answers.

Used by .github/workflows/competition.yml (see docs/competition.md). Two jobs, two trust levels:

    run    (API key, runs team code)     factory line ... ; factory ci export-submission submission/
    grade  (hidden answers, no team code) factory ci check-cases ... ; factory ci score submission/ ...

Everything that crosses the job boundary is data: grade only reads JSON.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from factory import answers, paths, workspace

# Points per component (sum = 100). Efficiency: full marks at or below the first value, zero at or
# above the second, and scaled by correctness. Calibrate on a baseline run before the day.
POINTS = {"correctness": 70, "efficiency": 15, "benchmark": 15}
COST_USD = (0.035, 0.21)   # half and three times the Gemma baseline line ($0.07 a run, 2026-11-27)
DURATION_S = (180.0, 900.0)  # baseline ~4 min in CI (3 min line + setup): full marks to 3, zero from 15. Check on a CI run
BENCHMARK_CASES = 3  # new, valid benchmark cases needed for full marks


def export_submission(dest: Path) -> Path | None:
    """Copy what the latest line run delivered (answers, summary, run summaries) into `dest`."""
    dest.mkdir(parents=True, exist_ok=True)
    summaries = sorted(paths.RUNS.glob("*/line_summary.json"))
    if not summaries:
        return None
    run = summaries[-1].parent
    shutil.copy(summaries[-1], dest / "line_summary.json")
    if (a := run / "workspace" / "output" / "answers.json").is_file():
        shutil.copy(a, dest / "answers.json")
    for s in run.glob("*/summary.json"):
        (dest / "runs" / s.parent.name).mkdir(parents=True, exist_ok=True)
        shutil.copy(s, dest / "runs" / s.parent.name / "summary.json")
    return dest


def valid_case(path: Path) -> tuple[bool, str]:
    """A benchmark case is valid when doing nothing scores 0 and the right answer scores 1."""
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
    return nothing == 0 and golden >= 0.99, f"nothing={nothing:.2f} right answer={golden:.2f}"


def _scale(x: float | None, lo_hi: tuple[float, float]) -> float:
    lo, hi = lo_hi
    return 0.0 if x is None else max(0.0, min(1.0, (hi - x) / (hi - lo)))


def score(submission: Path, right: Path, duration_s: float | None = None, cost_usd: float | None = None,
          cases: dict[str, Any] | None = None) -> dict[str, Any]:
    """Score one team. Reads only JSON: runs no team code."""
    given = answers.load(submission / "answers.json")
    per_q = answers.score(given, json.loads(right.read_text()))
    part = {"correctness": sum(per_q.values()) / len(per_q)}
    detail = {"correctness": ("no answers.json" if given is None else
                              ", ".join(f"{q} {s:.0%}" for q, s in per_q.items()))}

    # In the final, cost_usd is the spend of the team's final-only OpenRouter key, read by the grade
    # job: measured, outside the team's reach. Without it (practice) the cost comes from the run
    # summaries, which team code wrote. A missing cost counts as the worst cost.
    runs = [json.loads(p.read_text()) for p in sorted((submission / "runs").glob("*/summary.json"))]
    costs = [r.get("total_cost_usd") for r in runs]
    reported = sum(costs) if runs and all(c is not None for c in costs) else None
    cost = cost_usd if cost_usd is not None else reported
    part["efficiency"] = part["correctness"] * (_scale(cost, COST_USD) + _scale(duration_s, DURATION_S)) / 2
    detail["efficiency"] = (f"${cost:.2f}" if cost is not None else "cost unknown") + \
        (" (measured on the key)" if cost_usd is not None else " (from the runs)") + \
        (f", {duration_s / 60:.0f} min" if duration_s is not None else ", duration unknown") + ", scaled by correctness"

    ok = sum(1 for v in (cases or {}).values() if v[0])
    part["benchmark"] = min(ok, BENCHMARK_CASES) / BENCHMARK_CASES
    detail["benchmark"] = f"{ok} of {len(cases or {})} new cases valid (need {BENCHMARK_CASES})"

    points = {k: round(POINTS[k] * part[k], 1) for k in POINTS}
    return {"total": round(sum(points.values()), 1), "points": points, "max": POINTS, "detail": detail,
            "per_question": per_q, "cost_usd": cost, "reported_cost_usd": reported, "duration_s": duration_s}


def score_markdown(team: str, s: dict[str, Any]) -> str:
    lines = [f"### 🏁 `{team}` scores {s['total']:g} / 100", "", "| component | points | detail |", "|---|---:|---|"]
    lines += [f"| {k} | {s['points'][k]:g} / {s['max'][k]} | {s['detail'][k].replace('|', '/')} |" for k in s["max"]]
    return "\n".join(lines) + "\n"


def key_usage(key: str, settle_s: float = 5, tries: int = 12) -> float:
    """What an OpenRouter key has spent so far, in USD. Waits until two reads agree: usage can lag."""
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
