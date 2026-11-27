"""`factory`: run the line, benchmark the agents, score answers."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from factory import paths

console = Console()
STATIONS = ["intake", "implement", "review"]


@click.group()
def main() -> None:
    """Fernhill's dark factory: a request in, answers out."""


@main.command()
@click.option("--issue", type=click.Path(exists=True, path_type=Path), required=True, help="The request")
@click.option("--agent", "swaps", multiple=True, help="Swap a station: --agent review=agents/review-v2")
@click.option("--max-rework", type=int, default=None, help="Default: max_rework in agents/line.yaml")
def line(issue: Path, swaps: tuple[str, ...], max_rework: int | None) -> None:
    """Run the whole line on one request."""
    from factory.line import run_line

    agents = {k: Path(v) for k, v in (s.split("=", 1) for s in swaps)}
    out = asyncio.run(run_line(issue, agents, max_rework))
    console.print_json(json.dumps({k: out[k] for k in ("outcome", "total_cost_usd", "open_findings")}))
    console.print(f"answers: {Path(out['workspace']) / 'output' / 'answers.json'}")


@main.command()
@click.argument("run_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--answers", "right", type=click.Path(exists=True, path_type=Path), default=None,
              help="The right answers (default: the practice request's answers.json, found from the issue)")
def score(run_dir: Path, right: Path | None) -> None:
    """Score a line run, the way the final does (without the benchmark points)."""
    from factory import competition

    summary = json.loads((run_dir / "line_summary.json").read_text())
    right = right or next((p.parent / "answers.json" for p in paths.PRODUCTS.glob("*/issue.md")
                           if p.read_text() == (run_dir / "workspace" / "input" / "issue.md").read_text()), None)
    if not right:
        raise SystemExit("pass --answers: this run's issue is not one of the practice requests")
    from datetime import datetime

    sub = run_dir / "submission"
    (sub / "runs").mkdir(parents=True, exist_ok=True)
    (sub / "answers.json").write_text(json.dumps(summary.get("answers")))
    for s in run_dir.glob("*/summary.json"):
        (sub / "runs" / s.parent.name).mkdir(exist_ok=True)
        (sub / "runs" / s.parent.name / "summary.json").write_text(s.read_text())
    started = datetime.strptime(run_dir.name[:15], "%Y%m%d-%H%M%S").timestamp()
    s = competition.score(sub, right, duration_s=(run_dir / "line_summary.json").stat().st_mtime - started)
    console.print(competition.score_markdown(run_dir.name, s), markup=False)


@main.command()
@click.argument("name", type=click.Choice(["spec", "review"]))
def schema(name: str) -> None:
    """Print the JSON schema of spec.json or review.json."""
    from factory.contracts import json_schema

    print(json_schema(name))


# -------------------------------------------------------------------- benchmark


@main.group()
def bench() -> None:
    """Benchmark one station on its cases (benchmark/cases/<station>/)."""


@bench.command("run")
@click.argument("stage", type=click.Choice(STATIONS))
@click.option("--agent", "agent_dir", type=click.Path(exists=True, path_type=Path), default=None,
              help="Agent folder to benchmark (default: agents/<stage>)")
@click.option("--case", "cases", multiple=True, help="Only these case ids (prefix match)")
@click.option("--oracle", is_flag=True, help="Grade the right answers instead of running an agent")
@click.option("--repeat", default=1, show_default=True, help="Runs per case (agents are not deterministic)")
@click.option("--parallel", default=3, show_default=True)
@click.option("--suite", type=click.Path(exists=True, path_type=Path), default=None,
              help="Another case folder (e.g. cases you keep out of the repository)")
@click.option("--label", default=None, help="Name for this version in the report")
def bench_run(stage: str, agent_dir: Path | None, cases: tuple[str, ...], oracle: bool, repeat: int,
              parallel: int, suite: Path | None, label: str | None) -> None:
    """Run a station's cases and grade them."""
    from benchmark.harness import run_stage

    out = asyncio.run(run_stage(stage, agent_dir, list(cases) or None, oracle, False, repeat, parallel, suite, label))
    t = Table("case", "score", "± stdev", "runs")
    for cid, c in out["cases"].items():
        t.add_row(cid, f"{c['mean']:.3f}", f"{c['stdev']:.3f}", str(len(c["runs"])))
    console.print(t)
    for r in out["runs"]:
        for g in r["grades"]:
            if g["score"] < 1:
                console.print(f"  {r['case']:<28} {g['name']:<18} {g['score']:.2f}  {g['detail'][:110]}", markup=False)
    console.print(f"[bold]{stage} · {out['label']} · score {out['score']:.3f} · ${out['total_cost_usd']:.2f} "
                  f"· {out['mean_turns']} turns/run · {out['mean_duration_s']}s/run[/bold]")
    console.print(f"runs in {out['bench_dir']}")


@bench.command("report")
@click.option("--stage", default=None)
def bench_report(stage: str | None) -> None:
    """Every recorded benchmark run (benchmark/results/), best first."""
    from benchmark.harness import load_results

    t = Table("finished", "stage", "label", "fingerprint", "score", "$ total", "$/run", "turns", "s/run", "cases")
    for r in sorted(load_results(), key=lambda r: (r["stage"], -r["score"])):
        if stage and r["stage"] != stage:
            continue
        t.add_row(r["finished_at"][5:16], r["stage"], r["label"], str(r.get("agent_fingerprint")), f"{r['score']:.3f}",
                  f"{r['total_cost_usd']:.2f}", f"{r['mean_cost_usd']:.2f}", str(r["mean_turns"]),
                  str(r["mean_duration_s"]), str(len(r["cases"])))
    console.print(t)


@bench.command("check")
@click.argument("case_files", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
def bench_check(case_files: tuple[Path, ...]) -> None:
    """Check that a case is valid: doing nothing scores 0, the right answer scores 1."""
    from factory.competition import valid_case

    for f in case_files:
        ok, why = valid_case(f)
        console.print(f"{'[green]valid[/green]' if ok else '[red]invalid[/red]'}  {f}  {why}")


# -------------------------------------------------------------------- the final (CI)


@main.group()
def ci() -> None:
    """Steps of the competition workflow."""


@ci.command("export-submission")
@click.argument("dest", type=click.Path(path_type=Path))
def ci_export(dest: Path) -> None:
    from factory.competition import export_submission

    export_submission(dest)


@ci.command("report")
def ci_report() -> None:
    """Write the issue comment for the latest line run to factory-out/comment.md; print the outcome."""
    from factory.line import report_markdown

    summary = json.loads(sorted(paths.RUNS.glob("*/line_summary.json"))[-1].read_text())
    Path("factory-out").mkdir(exist_ok=True)
    Path("factory-out/comment.md").write_text(report_markdown(summary))
    print(summary["outcome"])


@ci.command("check-cases")
@click.argument("case_files", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--out", type=click.Path(path_type=Path), required=True)
def ci_check_cases(case_files: tuple[Path, ...], out: Path) -> None:
    """Validate a team's new cases; write {case: [valid, why]}."""
    from factory.competition import valid_case

    out.write_text(json.dumps({str(f): valid_case(f) for f in case_files}, indent=2))


@ci.command("score")
@click.argument("submission", type=click.Path(path_type=Path))
@click.option("--answers", "right", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--cases", type=click.Path(path_type=Path), default=None, help="Output of check-cases")
@click.option("--duration-s", type=float, default=None)
@click.option("--cost-usd", type=float, default=None, help="Measured spend of the team's key")
@click.option("--team", default="team")
def ci_score(submission: Path, right: Path, cases: Path | None, duration_s: float | None, cost_usd: float | None,
             team: str) -> None:
    from factory import competition

    c = json.loads(cases.read_text()) if cases and cases.exists() else {}
    s = competition.score(submission, right, duration_s, cost_usd, c)
    out = Path("factory-out")
    out.mkdir(exist_ok=True)
    (out / "score.json").write_text(json.dumps(s, indent=2))
    (out / "score.md").write_text(competition.score_markdown(team, s))
    console.print(competition.score_markdown(team, s), markup=False)


@ci.command("key-usage")
def ci_key_usage() -> None:
    """Print what the key in LLM_API_KEY has spent, in USD."""
    from factory.competition import key_usage

    print(key_usage(os.environ["LLM_API_KEY"]))


if __name__ == "__main__":
    main()
