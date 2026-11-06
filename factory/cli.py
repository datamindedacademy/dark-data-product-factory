"""`factory` command line."""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from factory import paths, workspace

console = Console()


@click.group()
def main() -> None:
    """Dark data product factory: agents that turn requests into data products."""


# ----------------------------------------------------------------------- setup


@main.command()
def setup() -> None:
    """Generate the synthetic warehouse and build the base dbt project."""
    paths.WAREHOUSE_DB.unlink(missing_ok=True)
    console.print("[cyan]Generating raw data...[/cyan]")
    workspace.sh([sys.executable, str(paths.ROOT / "scripts" / "generate_data.py"), "--db", str(paths.WAREHOUSE_DB)],
                 paths.ROOT)
    console.print("[cyan]dbt build...[/cyan]")
    r = workspace.sh([paths.tool("dbt"), "build", "--quiet"], paths.WAREHOUSE, check=False)
    if r.returncode != 0:
        console.print(r.stdout[-3000:])
        raise SystemExit("dbt build failed")
    workspace.sh([paths.tool("dbt"), "parse", "--quiet"], paths.WAREHOUSE)
    v = workspace.sh([paths.tool("dct"), "--no-send-anonymous-usage-stats", "validate"], paths.WAREHOUSE, check=False)
    console.print(v.stdout.strip())
    console.print(f"[green]Warehouse ready:[/green] {paths.WAREHOUSE_DB}")


# ------------------------------------------------------------------- utilities


@main.command()
@click.argument("kind", type=click.Choice(["spec", "review", "governance", "line_manager"]))
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def validate(kind: str, file: Path) -> None:
    """Validate an artifact against its contract (used by the agents themselves)."""
    from factory.contracts import SCHEMAS

    text = file.read_text()
    data = yaml.safe_load(text) if file.suffix in (".yaml", ".yml") else json.loads(text)
    try:
        SCHEMAS[kind].model_validate(data)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]INVALID[/red] {file}:\n{exc}")
        raise SystemExit(1) from exc
    console.print(f"[green]OK[/green]: {file} is a valid {kind}")


@main.command()
@click.argument("spec", type=click.Path(exists=True, path_type=Path))
@click.option("--db", type=click.Path(exists=True, path_type=Path), default=None,
              help="DuckDB file (default: warehouse/warehouse.duckdb next to the spec's repo)")
def accept(spec: Path, db: Path | None) -> None:
    """Run a spec's executable acceptance checks."""
    from factory.acceptance import run_acceptance
    from factory.contracts import DataProductSpec

    db = db or Path("warehouse/warehouse.duckdb")
    report = run_acceptance(DataProductSpec.load(spec), db)
    console.print(report.as_text(), markup=False)
    raise SystemExit(0 if report.passed == report.total else 1)


@main.command()
@click.option("--project", type=click.Path(exists=True, path_type=Path), default=paths.WAREHOUSE)
@click.option("--product", default=None, help="Data product id: scopes the Fernhill rules (--tag data_product=...)")
@click.option("--json", "as_json", is_flag=True, help="Print the Fernhill rule violations as JSON instead")
def checkup(project: Path, product: str | None, as_json: bool) -> None:
    """Run checkup on the dbt project (dbt parse + `checkup run`, config in checkup.yaml)."""
    from factory.tools import checkup as ck

    workspace.sh([paths.tool("dbt"), "parse", "--quiet"], project)
    if as_json:
        result = ck.run(project, product)
        console.print_json(json.dumps(result))
        raise SystemExit(1 if result["violations"] else 0)
    res = ck.checkup_cli(project, product)
    console.print(res.stdout, end="", markup=False, highlight=False)
    raise SystemExit(res.returncode)


# ------------------------------------------------------------------ run agents


@main.command()
@click.argument("stage", type=click.Choice(["intake", "implement", "review", "governance", "bi", "line_manager"]))
@click.option("--agent-dir", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--case", "case_id", default=None, help="Benchmark case id to set the workspace up from")
@click.option("--issue", type=click.Path(exists=True, path_type=Path), default=None, help="intake: issue markdown")
def run(stage: str, agent_dir: Path | None, case_id: str | None, issue: Path | None) -> None:
    """Run one agent once, in a fresh workspace (from a benchmark case or an issue)."""
    from benchmark.core import load_cases
    from benchmark.harness import STAGES
    from factory.runner import run_agent_sync

    run_dir = paths.RUNS / workspace.new_run_id(stage)
    ws = workspace.create(run_dir)
    ctx = {}
    if case_id:
        case = next((c for c in load_cases(stage) if c.id == case_id), None)
        if not case:
            raise SystemExit(f"no {stage} case {case_id!r}")
        ctx = STAGES[stage].setup(case, ws)
    elif issue and stage == "intake":
        workspace.copy_db(ws)
        shutil.copy(issue, ws / "input" / "issue.md")
    else:
        raise SystemExit("pass --case <id> (see `factory bench list`) or, for intake, --issue <file>")
    summary = run_agent_sync(agent_dir or paths.AGENTS / stage, ws, run_dir, ctx={**ctx, "repo_root": paths.ROOT},
                             meta={"stage": stage, "case": case_id or (issue.stem if issue else None)})
    console.print_json(json.dumps({k: summary.get(k) for k in
                                   ("status", "total_cost_usd", "num_turns", "duration_ms", "tool_calls", "missing_outputs")}))
    if case_id:
        from benchmark.core import weighted

        grades = STAGES[stage].grade(case, ws)
        for g in grades:
            console.print(f"  {g.name:<24} {g.score:.2f} (w{g.weight:g})  {g.detail[:120]}", markup=False)
        console.print(f"[bold]score {weighted(grades):.3f}[/bold]")
    console.print(f"workspace: {ws}\ntrace:     {run_dir / 'trace.jsonl'}")


@main.command()
@click.option("--issue", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--agent", "overrides", multiple=True, help="Swap a station: --agent bi=agents/bi-v2")
@click.option("--max-rework", default=1, show_default=True)
@click.option("--stop-after", type=click.Choice(["intake", "implement", "review", "governance"]), default=None)
def e2e(issue: Path, overrides: tuple[str, ...], max_rework: int, stop_after: str | None) -> None:
    """Run the whole factory line on one issue."""
    from factory.e2e import run_line

    agents = {k: Path(v) for k, v in (o.split("=", 1) for o in overrides)}
    summary = asyncio.run(run_line(issue, agents, max_rework, stop_after))
    console.print_json(json.dumps(summary, default=str))


# ---------------------------------------------------------------------------- ci


@main.group()
def ci() -> None:
    """Stations as CI steps (used by .github/workflows/factory-*.yml; runnable locally).

    Each step works on the current checkout, writes markdown + JSON to factory-out/
    (FACTORY_OUT) and step outputs to $GITHUB_OUTPUT.
    """


_spec_opt = click.option("--spec", "spec", type=click.Path(exists=True, path_type=Path), required=True,
                         help="Spec in the checkout, e.g. warehouse/specs/<id>.yaml")


@ci.command("intake")
@click.option("--issue-file", type=click.Path(exists=True, path_type=Path), required=True,
              help="Issue title, body and comments as markdown (the workflow writes it with `gh issue view`)")
def ci_intake(issue_file: Path) -> None:
    """Issue -> spec. Writes warehouse/specs/<id>.yaml when the spec is ready."""
    from factory import ci as c

    spec = c.intake(issue_file)
    raise SystemExit(0 if spec else 1)


@ci.command("implement")
@_spec_opt
@click.option("--feedback", type=click.Path(path_type=Path), default=None, help="Findings of a previous round")
def ci_implement(spec: Path, feedback: Path | None) -> None:
    """Spec -> dbt models in warehouse/models/marts/<id>/ of the checkout."""
    from factory import ci as c

    c.implement(spec, feedback)


@ci.command("bi")
@_spec_opt
def ci_bi(spec: Path) -> None:
    """Spec + models -> warehouse/charts/<id>.yml in the checkout."""
    from factory import ci as c

    c.bi(spec)


@ci.command("checks")
@_spec_opt
def ci_checks(spec: Path) -> None:
    """Deterministic gates, no LLM: dbt build, acceptance checks, checkup, dct validate."""
    from factory import ci as c

    raise SystemExit(0 if c.checks(spec) else 1)


@ci.command("review")
@_spec_opt
@click.option("--base", default="origin/main", show_default=True, help="Git ref the change is compared with")
@click.option("--pr-body", type=click.Path(path_type=Path), default=None)
def ci_review(spec: Path, base: str, pr_body: Path | None) -> None:
    """Review the checkout against --base. Writes review.md / review.json."""
    from factory import ci as c

    raise SystemExit(0 if c.review(spec, base, pr_body) else 1)


@ci.command("governance")
@click.option("--product", required=True)
def ci_governance(product: str) -> None:
    """Check the product against the standards. Writes governance.md / governance.json."""
    from factory import ci as c

    raise SystemExit(0 if c.governance(product) else 1)


@ci.command("feedback")
def ci_feedback() -> None:
    """Merge checks/review/governance findings into factory-out/feedback.md."""
    from factory import ci as c

    c.feedback()


@ci.command("line-manager")
@click.option("--runs", "runs_dir", type=click.Path(exists=True, path_type=Path), required=True)
def ci_line_manager(runs_dir: Path) -> None:
    """Traces of recent pipeline runs -> factory-out/line_manager.md."""
    from factory import ci as c

    raise SystemExit(0 if c.line_manager(runs_dir) else 1)


@ci.command("collect-runs")
@click.argument("dest", type=click.Path(path_type=Path))
def ci_collect_runs(dest: Path) -> None:
    """Copy run summaries + traces (no workspaces) to DEST for artifact upload."""
    from factory import ci as c

    console.print(f"collected {c.collect_runs(dest)} runs into {dest}")


# -------------------------------------------------------------------- benchmark


@main.group()
def bench() -> None:
    """Benchmark the agents of the line."""


@bench.command("list")
@click.option("--suite", type=click.Path(exists=True, path_type=Path), default=None)
def bench_list(suite: Path | None) -> None:
    """List benchmark cases."""
    from benchmark.core import load_cases
    from benchmark.harness import STAGES

    t = Table("stage", "case", "description")
    for s in STAGES:
        for c in load_cases(s, suite):
            t.add_row(s, c.id, c.description.strip().split(". ")[0][:90])
    console.print(t)


@bench.command("run")
@click.argument("stage", type=click.Choice(["intake", "implement", "review", "governance", "bi", "line_manager"]))
@click.option("--agent-dir", type=click.Path(exists=True, path_type=Path), default=None,
              help="Agent variant to benchmark (default: agents/<stage>)")
@click.option("--case", "cases", multiple=True, help="Only these case ids (prefix match)")
@click.option("--oracle", is_flag=True, help="Grade the golden outputs instead of running an agent")
@click.option("--judge", is_flag=True, help="Enable LLM-as-judge graders")
@click.option("--repeat", default=1, show_default=True, help="Runs per case (agents are not deterministic)")
@click.option("--parallel", default=2, show_default=True)
@click.option("--suite", type=click.Path(exists=True, path_type=Path), default=None,
              help="Alternative case directory (e.g. the facilitators' hold-out set)")
@click.option("--label", default=None, help="Name for this variant in the report")
def bench_run(stage: str, agent_dir: Path | None, cases: tuple[str, ...], oracle: bool, judge: bool, repeat: int,
              parallel: int, suite: Path | None, label: str | None) -> None:
    """Run (or oracle) a stage's benchmark cases and grade them."""
    from benchmark.harness import run_stage

    out = asyncio.run(run_stage(stage, agent_dir, list(cases) or None, oracle, judge, repeat, parallel, suite, label))
    t = Table("case", "score", "± stdev", "runs")
    for cid, c in out["cases"].items():
        t.add_row(cid, f"{c['mean']:.3f}", f"{c['stdev']:.3f}", str(len(c["runs"])))
    console.print(t)
    for r in out["runs"]:
        for g in r["grades"]:
            if g["score"] < 1:
                console.print(f"  {r['case']:<28} {g['name']:<24} {g['score']:.2f}  {g['detail'][:110]}", markup=False)
    console.print(f"[bold]{stage} · {out['label']} · score {out['score']:.3f} · ${out['total_cost_usd']:.2f} "
                  f"· {out['mean_turns']} turns/run · {out['mean_duration_s']}s/run[/bold]")
    console.print(f"runs in {out['bench_dir']}")


@bench.command("report")
@click.option("--stage", default=None)
@click.option("--markdown", is_flag=True, help="Print a markdown table (for CI summaries and PR comments)")
def bench_report(stage: str | None, markdown: bool) -> None:
    """Leaderboard of every recorded benchmark run (benchmark/results/)."""
    from benchmark.harness import load_results

    if markdown:
        rows = [r for r in sorted(load_results(), key=lambda r: (r["stage"], -r["score"])) if not stage or r["stage"] == stage]
        print("| stage | label | fingerprint | score | $ total | $/run | turns | s/run |\n|---|---|---|---:|---:|---:|---:|---:|")
        for r in rows:
            print(f"| {r['stage']} | {r['label']} | `{r.get('agent_fingerprint')}` | {r['score']:.3f} | {r['total_cost_usd']:.2f} "
                  f"| {r['mean_cost_usd']:.2f} | {r['mean_turns']} | {r['mean_duration_s']} |")
        return

    t = Table("finished", "stage", "label", "fingerprint", "score", "$ total", "$/run", "turns", "s/run", "cases")
    for r in sorted(load_results(), key=lambda r: (r["stage"], -r["score"])):
        if stage and r["stage"] != stage:
            continue
        t.add_row(r["finished_at"][5:16], r["stage"], r["label"], str(r.get("agent_fingerprint")), f"{r['score']:.3f}",
                  f"{r['total_cost_usd']:.2f}", f"{r['mean_cost_usd']:.2f}", str(r["mean_turns"]),
                  str(r["mean_duration_s"]), str(len(r["cases"])))
    console.print(t)


if __name__ == "__main__":
    main()
