"""End-to-end factory line: issue -> spec -> models -> review -> governance -> dashboard.

All stations work in one workspace, the way they would in one repository:

    intake      input/issue.md            -> output/spec.yaml   (stop unless status == ready)
    implement   input/spec.yaml           -> warehouse/models/marts/<id>/  on branch `feature`
    review      git diff main...feature   -> output/review.json      } in parallel; governance works
    governance  the product               -> output/governance.json  } in a copy of the workspace
    (rework)    findings -> input/feedback.md -> implement again (max_rework in agents/line.yaml)
    bi          spec + built models       -> warehouse/charts/<id>.yml

Any station can be swapped for your team's agent with --agent <stage>=<dir>.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from factory import paths, workspace
from factory.acceptance import run_acceptance
from factory.contracts import DataProductSpec, GovernanceReport, Review
from factory.runner import run_agent

console = Console()


def line_max_rework() -> int:
    """The team's rework limit from agents/line.yaml (1 when the file or the key is missing)."""
    f = paths.AGENTS / "line.yaml"
    return int((yaml.safe_load(f.read_text()) or {}).get("max_rework", 1)) if f.exists() else 1


async def run_line(issue: Path, agents: dict[str, Path] | None = None, max_rework: int | None = None,
                   stop_after: str | None = None) -> dict[str, Any]:
    if max_rework is None:
        max_rework = line_max_rework()
    agents = {s: paths.AGENTS / s for s in ["intake", "implement", "review", "governance", "bi"]} | (agents or {})
    run_dir = paths.RUNS / workspace.new_run_id("e2e")
    ws = workspace.create(run_dir)
    workspace.copy_db(ws)
    shutil.copy(issue, ws / "input" / "issue.md")
    log: list[dict[str, Any]] = []
    console.rule(f"[bold]factory line[/bold] {run_dir}")

    async def station(stage: str, n: int = 1, at: Path | None = None, **ctx: Any) -> dict[str, Any]:
        console.print(f"[cyan]▶ {stage}[/cyan] (round {n})")
        s = await run_agent(agents[stage], at or ws, run_dir / f"{stage}-{n}", ctx={"repo_root": paths.ROOT, **ctx},
                            meta={"stage": stage, "round": n, "case": issue.stem})
        log.append({"stage": stage, "round": n, "status": s["status"], "cost_usd": s.get("total_cost_usd"),
                    "turns": s.get("num_turns"), "duration_ms": s.get("duration_ms")})
        console.print(f"  {s['status']} · ${s.get('total_cost_usd') or 0:.2f} · {s.get('num_turns')} turns")
        return s

    def done(outcome: str, **extra: Any) -> dict[str, Any]:
        summary = {"outcome": outcome, "workspace": str(ws), "stations": log,
                   "total_cost_usd": round(sum(x["cost_usd"] or 0 for x in log), 4), **extra}
        (run_dir / "e2e_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        console.rule(f"[bold]{outcome}[/bold] · ${summary['total_cost_usd']:.2f}")
        return summary

    # 1. intake
    await station("intake")
    try:
        spec = DataProductSpec.load(ws / "output" / "spec.yaml")
    except Exception as exc:  # noqa: BLE001
        return done("intake_failed", error=str(exc)[:500])
    if spec.status != "ready":
        console.print("[yellow]Spec is not ready - this would go back to the requester:[/yellow]")
        for q in spec.open_questions or [spec.infeasible_reason]:
            console.print(f"  • {q}")
        return done(f"stopped_{spec.status}", open_questions=spec.open_questions)
    shutil.copy(ws / "output" / "spec.yaml", ws / "input" / "spec.yaml")
    workspace.commit(ws, f"spec: {spec.id}", branch="feature")
    if stop_after == "intake":
        return done("stopped_after_intake")

    # 2. implement <-> review / governance loop
    feedback = ws / "input" / "feedback.md"
    for rnd in range(1, max_rework + 2):
        impl = await station("implement", rnd, product_id=spec.id)
        workspace.commit(ws, f"implement {spec.id} (round {rnd})")
        (ws / "input" / "pr.md").write_text(f"# Add data product `{spec.id}`\n\n{impl.get('final_text', '')}\n")
        if stop_after == "implement":
            break
        # Review and governance run side by side, as in factory-pr.yml. Governance gets its own copy of the
        # workspace so the two agents never share warehouse.duckdb (DuckDB allows one writer) or .claude/.
        gov_ws = shutil.copytree(ws, run_dir / f"governance-{rnd}-workspace", symlinks=True)
        await asyncio.gather(station("review", rnd, product_id=spec.id),
                             station("governance", rnd, at=gov_ws, product_id=spec.id))
        problems = []
        try:
            review = Review.model_validate_json((ws / "output" / "review.json").read_text())
            if review.verdict == "request_changes":
                problems += [f"- [review/{f.severity}] {f.file}: {f.message}" for f in review.findings]
        except Exception as exc:  # noqa: BLE001
            problems.append(f"- review output invalid: {exc}")
        try:
            gov = GovernanceReport.model_validate_json((gov_ws / "output" / "governance.json").read_text())
            problems += [f"- [governance/{v.rule_id}] {v.model} {v.column or ''}: {v.message}" for v in gov.violations]
        except Exception as exc:  # noqa: BLE001
            problems.append(f"- governance output invalid: {exc}")
        if not problems:
            break
        if rnd > max_rework:
            console.print(f"[red]Still {len(problems)} open findings after {max_rework} rework round(s).[/red]")
            break
        feedback.write_text("# Findings to address\n\n" + "\n".join(problems) + "\n")
        console.print(f"[yellow]{len(problems)} findings -> rework[/yellow]")

    acceptance = run_acceptance(spec, ws / "warehouse" / "warehouse.duckdb")
    console.print(acceptance.as_text())
    if stop_after in ("implement", "review", "governance"):
        return done(f"stopped_after_{stop_after}", acceptance=acceptance.score)

    # 3. dashboard
    await station("bi", product_id=spec.id)
    board = ws / "warehouse" / "charts" / f"{spec.id}.yml"
    valid = board.exists() and workspace.dct(ws, "validate", f"charts/{spec.id}.yml").returncode == 0
    if valid:
        workspace.dct(ws, "render", f"charts/{spec.id}.yml", "--format", "html", "--output", f"renders/{spec.id}.html")
    workspace.commit(ws, f"dashboard {spec.id}")
    return done("delivered" if valid else "dashboard_invalid", product_id=spec.id, acceptance=acceptance.score,
                dashboard=str(ws / "warehouse" / "renders" / f"{spec.id}.html") if valid else None)
