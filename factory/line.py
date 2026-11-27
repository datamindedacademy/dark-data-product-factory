"""The factory line: a request in, answers out, nobody in the loop.

    intake      input/issue.md                       -> output/spec.json     the line stops unless "ready"
    implement   input/spec.json (+ input/feedback.md) -> output/answers.json
    review      spec + answers + code                -> output/review.json   } checkers, side by side
    (rework)    findings -> input/feedback.md -> implement again, up to max_rework times

agents/line.yaml lists the stations. Add your own agent anywhere: before implement it runs once, in
order; after implement it is a checker like review, and writes output/<name>.json in the review format.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from factory import answers, paths, workspace
from factory.contracts import Review, Spec
from factory.runner import run_agent

console = Console()


def config(agents_dir: Path | None = None) -> dict[str, Any]:
    f = (agents_dir or paths.AGENTS) / "line.yaml"
    raw = (yaml.safe_load(f.read_text()) or {}) if f.exists() else {}
    stations = raw.get("stations") or ["intake", "implement", "review"]
    if stations[0] != "intake" or "implement" not in stations:
        raise SystemExit("agents/line.yaml: the line starts with intake and has an implement station")
    return {"stations": stations, "max_rework": int(raw.get("max_rework", 1))}


async def run_line(issue: Path, agents: dict[str, Path] | None = None, max_rework: int | None = None,
                   agents_dir: Path | None = None) -> dict[str, Any]:
    cfg = config(agents_dir)
    max_rework = cfg["max_rework"] if max_rework is None else max_rework
    stations = cfg["stations"]
    agent_dir = {s: (agents_dir or paths.AGENTS) / s for s in stations} | (agents or {})
    run_dir = paths.RUNS / workspace.new_run_id("line")
    ws = workspace.create(run_dir)
    shutil.copy(issue, ws / "input" / "issue.md")
    tpl = answers.template(issue.read_text())
    log: list[dict[str, Any]] = []
    console.rule(f"[bold]factory line[/bold] {run_dir}")

    async def station(name: str, n: int = 1) -> None:
        console.print(f"[cyan]▶ {name}[/cyan] (round {n})")
        s = await run_agent(agent_dir[name], ws, run_dir / f"{name}-{n}", meta={"stage": name, "round": n})
        log.append({"stage": name, "round": n, "status": s["status"], "cost_usd": s.get("total_cost_usd"),
                    "turns": s.get("num_turns"), "duration_ms": s.get("duration_ms"), "error": s.get("error")})
        console.print(f"  {s['status']} · ${s.get('total_cost_usd') or 0:.3f} · {s.get('num_turns')} turns")

    def done(outcome: str, open_findings: list[str] | None = None, **extra: Any) -> dict[str, Any]:
        out = answers.load(ws / "output" / "answers.json")
        summary = {"outcome": outcome, "workspace": str(ws), "issue": issue.name, "stations": log,
                   "total_cost_usd": round(sum(x["cost_usd"] or 0 for x in log), 4),
                   "open_findings": open_findings or [], "answers": out, **extra}
        (run_dir / "line_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        console.rule(f"[bold]{outcome}[/bold] · ${summary['total_cost_usd']:.3f}")
        return summary

    first, rest = stations[: stations.index("implement")], stations[stations.index("implement") + 1:]
    for name in first:
        await station(name)
        if name == "intake":
            try:
                spec = Spec.load(ws / "output" / "spec.json")
            except Exception as exc:  # noqa: BLE001
                return done("intake_failed", error=str(exc)[:500])
            if spec.status != "ready":
                for q in spec.open_questions or [spec.reason]:
                    console.print(f"  [yellow]• {q}[/yellow]")
                return done(f"stopped_{spec.status}", open_questions=spec.open_questions, reason=spec.reason)
            shutil.copy(ws / "output" / "spec.json", ws / "input" / "spec.json")

    problems: list[str] = []
    for rnd in range(1, max_rework + 2):
        await station("implement", rnd)
        problems = [f"- [answers.json] {p}" for p in
                    answers.shape_problems(answers.load(ws / "output" / "answers.json"), tpl)]
        for c in rest:  # a checker that fails to write must not pass on last round's verdict
            (ws / "output" / f"{c}.json").unlink(missing_ok=True)
        await asyncio.gather(*[station(c, rnd) for c in rest])
        for c in rest:
            try:
                r = Review.load(ws / "output" / f"{c}.json")
            except Exception as exc:  # noqa: BLE001
                problems.append(f"- [{c}] output/{c}.json is missing or invalid: {str(exc)[:200]}")
                continue
            if r.verdict == "request_changes":
                problems += [f"- [{c}/{f.severity}] {f.question}: {f.message}" for f in r.findings] or \
                            [f"- [{c}] requests changes: {r.summary}"]
        if not problems or rnd > max_rework:
            break
        (ws / "input" / "feedback.md").write_text("# Findings to address\n\n" + "\n".join(problems) + "\n")
        console.print(f"[yellow]{len(problems)} findings -> rework[/yellow]")
    return done("answered" if not problems else "answered_with_open_findings", problems)


def report_markdown(summary: dict[str, Any]) -> str:
    """The comment the factory posts on the issue."""
    o = summary["outcome"]
    if o.startswith("stopped_"):
        lines = ["🙋 The factory needs more information before it can answer:", ""]
        lines += [f"- {q}" for q in summary.get("open_questions") or [summary.get("reason") or "(no reason given)"]]
        lines += ["", "Reply on this issue and the factory runs again with the whole thread."]
    elif o == "intake_failed":
        lines = [f"❌ The intake station did not produce a valid spec: `{summary.get('error', '')[:300]}`"]
    else:
        lines = ["✅ The factory's answers:" if o == "answered" else
                 "⚠️ The factory's answers. The checkers still had findings, see below.", "", "```json",
                 json.dumps(summary.get("answers"), indent=2), "```"]
        if summary.get("open_findings"):
            lines += ["", "Open findings:", "", *summary["open_findings"]]
    lines += ["", f"Cost ${summary['total_cost_usd']:.2f} · stations: " +
              ", ".join(f"{s['stage']} {s['round']}" for s in summary["stations"])]
    return "\n".join(lines) + "\n"
