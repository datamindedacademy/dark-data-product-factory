"""Benchmark harness: run an agent (or the oracle) on every case of a stage and grade it.

    factory bench run intake                    # baseline agent, all intake cases
    factory bench run intake --agent-dir agents/intake-v2 --repeat 3
    factory bench run implement --oracle        # golden outputs: checks the graders
    factory bench report                        # compare all recorded runs
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from benchmark.core import Case, Grade, Stage, grades_json, load_cases, weighted
from benchmark.stages.implement import Implement
from benchmark.stages.intake import Intake
from benchmark.stages.review import ReviewStage
from factory import paths, workspace

STAGES: dict[str, Stage] = {s.name: s for s in [Intake(), Implement(), ReviewStage()]}


async def run_case(stage: Stage, case: Case, bench_dir: Path, agent_dir: Path | None, oracle: bool,
                   judge: bool, rep: int) -> dict[str, Any]:
    run_dir = bench_dir / f"{case.id}-r{rep}"
    ws = await asyncio.to_thread(workspace.create, run_dir)
    ctx = await asyncio.to_thread(stage.setup, case, ws)
    meta = {"run_id": run_dir.name, "stage": stage.name, "case": case.id, "repeat": rep,
            "started_at": datetime.now().isoformat(timespec="seconds")}
    t0 = time.time()
    if oracle:
        await asyncio.to_thread(stage.oracle, case, ws)
        summary = {**meta, "agent": "oracle", "agent_fingerprint": "oracle", "status": "ok", "total_cost_usd": 0.0,
                   "num_turns": 0, "duration_ms": int((time.time() - t0) * 1000)}
    else:
        from factory.runner import run_agent

        summary = await run_agent(agent_dir or paths.AGENTS / stage.agent, ws, run_dir,
                                  ctx=ctx, meta=meta)
    try:
        grades = await asyncio.to_thread(stage.grade, case, ws, judge)
    except Exception as exc:  # noqa: BLE001 - a grader crash should not kill the whole benchmark
        grades = [Grade("grader_error", 0, 1, f"{type(exc).__name__}: {exc}")]
    summary["score"] = round(weighted(grades), 4)
    summary["grades"] = grades_json(grades)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


async def run_stage(stage_name: str, agent_dir: Path | None = None, cases: list[str] | None = None,
                    oracle: bool = False, judge: bool = False, repeat: int = 1, parallel: int = 2,
                    suite: Path | None = None, label: str | None = None) -> dict[str, Any]:
    stage = STAGES[stage_name]
    selected = load_cases(stage_name, suite, cases)
    if not selected:
        raise SystemExit(f"no cases found for stage {stage_name!r}")
    tag = label or ("oracle" if oracle else Path(agent_dir or stage.agent).name)
    bench_dir = paths.RUNS / f"bench-{datetime.now():%Y%m%d-%H%M%S}-{stage_name}-{tag}"
    sem = asyncio.Semaphore(parallel)

    async def guarded(case: Case, rep: int) -> dict[str, Any]:
        async with sem:
            return await run_case(stage, case, bench_dir, agent_dir, oracle, judge, rep)

    results = await asyncio.gather(*[guarded(c, r) for c in selected for r in range(repeat)])
    out = summarise(stage_name, tag, results, bench_dir)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    (paths.RESULTS / f"{bench_dir.name}.json").write_text(json.dumps(out, indent=2, default=str))
    return out


def summarise(stage: str, tag: str, results: list[dict[str, Any]], bench_dir: Path) -> dict[str, Any]:
    by_case: dict[str, list[dict]] = {}
    for r in results:
        by_case.setdefault(r["case"], []).append(r)
    cases = {}
    for cid, rs in by_case.items():
        scores = [r["score"] for r in rs]
        cases[cid] = {"mean": round(statistics.mean(scores), 4),
                      "stdev": round(statistics.stdev(scores), 4) if len(scores) > 1 else 0.0,
                      "runs": [r["run_id"] for r in rs]}
    costs = [r.get("total_cost_usd") or 0 for r in results]
    return {
        "stage": stage, "label": tag, "bench_dir": str(bench_dir),
        "agent_fingerprint": results[0].get("agent_fingerprint"),
        "model": results[0].get("model"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "score": round(statistics.mean(c["mean"] for c in cases.values()), 4),
        "total_cost_usd": round(sum(costs), 4),
        "mean_cost_usd": round(statistics.mean(costs), 4),
        "mean_turns": round(statistics.mean(r.get("num_turns") or 0 for r in results), 1),
        "mean_duration_s": round(statistics.mean((r.get("duration_ms") or 0) / 1000 for r in results), 1),
        "cases": cases,
        "runs": [{k: r.get(k) for k in ("run_id", "case", "score", "total_cost_usd", "num_turns", "status", "grades")}
                 for r in results],
    }


def load_results() -> list[dict[str, Any]]:
    out = []
    for f in sorted(paths.RESULTS.glob("*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            continue
    return out
