"""The factory as a CI pipeline: one command per station, run from a repo checkout.

The GitHub Actions workflows in ``.github/workflows/factory-*.yml`` only do the
GitHub side (read issues, push branches, open PRs, post reviews). Every station
is a ``factory ci <station>`` command that

1. builds an isolated workspace from the *current checkout* (so it sees the
   branch's previous work),
2. runs the station's agent there (traces in ``runs/``, uploaded as artifacts),
3. copies the station's deliverable back into the checkout, and
4. writes markdown for GitHub plus ``key=value`` outputs to ``$GITHUB_OUTPUT``.

Because nothing here talks to GitHub, every station can be run and debugged on a
laptop exactly as CI runs it::

    factory ci intake --issue-file issue.md
    factory ci implement --spec warehouse/specs/category_performance.yaml
    factory ci bi --spec warehouse/specs/category_performance.yaml
    factory ci checks --spec warehouse/specs/category_performance.yaml
    factory ci review --spec warehouse/specs/category_performance.yaml --base origin/main
    factory ci governance --product category_performance
    factory ci feedback
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from factory import paths, workspace
from factory.acceptance import run_acceptance
from factory.contracts import DataProductSpec, GovernanceReport, LineManagerReport, Review



def out_dir() -> Path:
    return Path(os.environ.get("FACTORY_OUT", paths.ROOT / "factory-out"))


def specs_dir() -> Path:
    return paths.WAREHOUSE / "specs"


# ------------------------------------------------------------------------ helpers


def set_outputs(**kv: Any) -> None:
    """Write step outputs for GitHub Actions (and echo them for humans)."""
    lines = [f"{k}={v}" for k, v in kv.items()]
    for line in lines:
        print(f"::notice::{line}" if os.environ.get("GITHUB_ACTIONS") else line)
    if gh := os.environ.get("GITHUB_OUTPUT"):
        with open(gh, "a") as f:
            f.write("\n".join(lines) + "\n")


def _write(name: str, text: str) -> Path:
    out = out_dir()
    out.mkdir(parents=True, exist_ok=True)
    p = out / name
    p.write_text(text)
    return p


def _ensure_db() -> None:
    if not paths.WAREHOUSE_DB.exists():
        raise SystemExit("warehouse/warehouse.duckdb missing - run `factory setup` first")


def _run(stage: str, ws: Path, run_dir: Path, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    from factory.runner import run_agent_sync

    agent_dir = Path(os.environ.get(f"FACTORY_AGENT_{stage.upper()}") or paths.AGENTS / stage)
    summary = run_agent_sync(agent_dir, ws, run_dir, ctx={"repo_root": paths.ROOT, **(ctx or {})},
                             meta={"stage": stage, "ci_run": os.environ.get("GITHUB_RUN_ID"),
                                   "case": os.environ.get("FACTORY_CASE")})
    print(f"{stage}: {summary['status']} · ${summary.get('total_cost_usd') or 0:.2f} · {summary.get('num_turns')} turns")
    return summary


def checkout_workspace(stage: str) -> tuple[Path, Path]:
    """Fresh workspace whose ``main`` is the current checkout."""
    _ensure_db()
    run_dir = paths.RUNS / workspace.new_run_id(f"ci-{stage}")
    return workspace.create(run_dir), run_dir


def review_workspace(base_ref: str) -> tuple[Path, Path]:
    """Workspace with ``main`` = ``base_ref`` and branch ``feature`` = the current checkout."""
    _ensure_db()
    run_dir = paths.RUNS / workspace.new_run_id("ci-review")
    base = run_dir / "base"
    base.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", base_ref, "warehouse", "standards"], cwd=paths.ROOT,
                             capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(base)], input=archive.stdout, check=True)
    ws = workspace.create(run_dir, source=base)
    workspace.branch(ws, "feature")
    for child in (ws / "warehouse").iterdir():
        if child.name != "warehouse.duckdb":
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    shutil.copytree(paths.WAREHOUSE, ws / "warehouse", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("target", "logs", "renders", "dbt_packages", "*.duckdb*"))
    workspace.commit(ws, "changes under review")
    return ws, run_dir


def _sync_back(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
    if src.is_dir():
        shutil.copytree(src, dst)
    elif src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)


# ----------------------------------------------------------------------- markdown


def spec_markdown(spec: DataProductSpec) -> str:
    lines = [f"### 🏭 Intake: `{spec.id}` — {spec.title}", "", f"**Status:** `{spec.status}`", "", spec.purpose.strip(), ""]
    if spec.status == "ready":
        lines += ["**Business questions**", ""]
        lines += [f"- **{q.id}** {q.question} ({len(q.acceptance)} acceptance checks)" for q in spec.business_questions]
        lines += ["", "**Outputs:** " + ", ".join(f"`{o.name}` ({' × '.join(o.grain)})" for o in spec.outputs)]
        if spec.data_quality_notes:
            lines += ["", "<details><summary>Data quality notes</summary>", ""]
            lines += [f"- {n.issue} → {n.handling}" for n in spec.data_quality_notes]
            lines += ["", "</details>"]
        lines += ["", "The factory will now implement this and open a pull request."]
    else:
        if spec.infeasible_reason:
            lines += [f"**Why this cannot be built as asked:** {spec.infeasible_reason.strip()}", ""]
        if spec.open_questions:
            lines += ["**Questions for you** (reply in a comment and the factory will pick it up again):", ""]
            lines += [f"{i}. {q}" for i, q in enumerate(spec.open_questions, 1)]
    return "\n".join(lines) + "\n"


def review_markdown(review: Review) -> str:
    icon = "✅" if review.verdict == "approve" else "🔁"
    lines = [f"### {icon} Factory review: `{review.verdict}`", "", review.summary.strip(), "",
             f"Docs up to date: {'yes' if review.docs_up_to_date else '**no**'}", ""]
    if review.findings:
        lines += ["| severity | category | file | finding |", "|---|---|---|---|"]
        for f in review.findings:
            loc = f"`{f.file}{':' + str(f.line) if f.line else ''}`"
            msg = f.message.replace("|", "\\|").replace("\n", " ")
            if f.suggestion:
                msg += f"<br>💡 {f.suggestion.replace('|', '\\|').replace(chr(10), ' ')}"
            lines.append(f"| {f.severity} | {f.category} | {loc} | {msg} |")
    return "\n".join(lines) + "\n"


def governance_markdown(report: GovernanceReport) -> str:
    icon = "✅" if report.compliant else "⛔"
    lines = [f"### {icon} Governance: `{report.product_id}` {'is compliant' if report.compliant else 'violates the standards'}", ""]
    if report.violations:
        lines += ["| rule | model | column | violation |", "|---|---|---|---|"]
        lines += [f"| {v.rule_id} | `{v.model}` | {v.column or ''} | {v.message.replace('|', '\\|')} |" for v in report.violations]
    if report.checked_rules:
        lines += ["", "Rules checked: " + ", ".join(report.checked_rules)]
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------- stations


def intake(issue_file: Path) -> DataProductSpec | None:
    ws, run_dir = checkout_workspace("intake")
    shutil.copy(issue_file, ws / "input" / "issue.md")
    _run("intake", ws, run_dir)
    try:
        spec = DataProductSpec.load(ws / "output" / "spec.yaml")
    except Exception as exc:  # noqa: BLE001
        _write("comment.md", f"### 🏭 Intake failed\n\nThe intake agent did not produce a valid spec:\n\n```\n{str(exc)[:1500]}\n```\n")
        set_outputs(status="failed", product_id="")
        return None
    _write("spec.yaml", (ws / "output" / "spec.yaml").read_text())
    _write("comment.md", spec_markdown(spec))
    if spec.status == "ready":
        specs_dir().mkdir(parents=True, exist_ok=True)
        shutil.copy(ws / "output" / "spec.yaml", specs_dir() / f"{spec.id}.yaml")
    set_outputs(status=spec.status, product_id=spec.id, title=spec.title.replace("\n", " "))
    return spec


def implement(spec_path: Path, feedback: Path | None = None) -> dict[str, Any]:
    spec = DataProductSpec.load(spec_path)
    ws, run_dir = checkout_workspace("implement")
    shutil.copy(spec_path, ws / "input" / "spec.yaml")
    if feedback and feedback.exists() and feedback.read_text().strip():
        shutil.copy(feedback, ws / "input" / "feedback.md")
    summary = _run("implement", ws, run_dir, {"product_id": spec.id})
    rel = Path("warehouse/models/marts") / spec.id
    _sync_back(ws / rel, paths.ROOT / rel)
    _write("implement.md", f"### 🛠️ Implementation of `{spec.id}`\n\n{summary.get('final_text', '').strip()}\n")
    set_outputs(product_id=spec.id, changed=str((paths.ROOT / rel).exists()).lower())
    return summary


def bi(spec_path: Path) -> dict[str, Any]:
    spec = DataProductSpec.load(spec_path)
    ws, run_dir = checkout_workspace("bi")
    shutil.copy(spec_path, ws / "input" / "spec.yaml")
    workspace.dbt(ws, "build", "--quiet")
    summary = _run("bi", ws, run_dir, {"product_id": spec.id})
    rel = Path("warehouse/charts") / f"{spec.id}.yml"
    _sync_back(ws / rel, paths.ROOT / rel)
    set_outputs(board=str((paths.ROOT / rel).exists()).lower())
    return summary


def checks(spec_path: Path) -> bool:
    """Deterministic quality gates (no LLM): dbt build, acceptance, checkup, dct validate."""
    from factory.tools import checkup

    spec = DataProductSpec.load(spec_path)
    ws, _ = checkout_workspace("checks")
    results: list[tuple[str, bool, str]] = []
    build = workspace.dbt(ws, "build")
    results.append(("dbt build", build.returncode == 0, (build.stdout.strip().splitlines() or [""])[-1]))
    acc = run_acceptance(spec, ws / "warehouse" / "warehouse.duckdb")
    results.append(("acceptance checks", acc.passed == acc.total and acc.total > 0, f"{acc.passed}/{acc.total} passed"))
    workspace.dbt(ws, "parse", "--quiet")
    viol = checkup.run(ws / "warehouse", spec.id)["violations"]
    results.append(("checkup (Fernhill rules)", not viol,
                    "clean" if not viol else "; ".join(f"{v['rule_id']} {v['model']}" for v in viol[:8])))
    board = f"charts/{spec.id}.yml"
    if (ws / "warehouse" / board).exists():
        val = workspace.dct(ws, "validate", board)
        results.append(("dct validate", val.returncode == 0, (val.stdout + val.stderr).strip().splitlines()[-1][:200]))
    else:
        results.append(("dct validate", False, f"warehouse/{board} missing"))
    ok = all(r[1] for r in results)
    md = [f"### {'✅' if ok else '❌'} Factory checks for `{spec.id}`", "", "| gate | result | detail |", "|---|---|---|"]
    md += [f"| {n} | {'✅' if p else '❌'} | {d.replace('|', '/')} |" for n, p, d in results]
    md += ["", "<details><summary>Acceptance checks</summary>", "", "```", acc.as_text(), "```", "</details>"]
    _write("checks.md", "\n".join(md) + "\n")
    _write("checks.json", json.dumps({"ok": ok, "gates": [{"gate": n, "passed": p, "detail": d} for n, p, d in results],
                                      "acceptance": [r.__dict__ for r in acc.results]}, default=str, indent=2))
    set_outputs(checks_ok=str(ok).lower())
    return ok


def review(spec_path: Path, base_ref: str, pr_body: Path | None = None) -> Review | None:
    spec = DataProductSpec.load(spec_path)
    ws, run_dir = review_workspace(base_ref)
    shutil.copy(spec_path, ws / "input" / "spec.yaml")
    (ws / "input" / "pr.md").write_text(pr_body.read_text() if pr_body and pr_body.exists() else f"Adds data product `{spec.id}`.")
    workspace.dbt(ws, "build", "--quiet")
    workspace.dbt(ws, "parse", "--quiet")
    _run("review", ws, run_dir, {"product_id": spec.id})
    try:
        rev = Review.model_validate_json((ws / "output" / "review.json").read_text())
    except Exception as exc:  # noqa: BLE001
        _write("review.md", f"### ⚠️ Factory review failed\n\n```\n{str(exc)[:1500]}\n```\n")
        set_outputs(verdict="failed")
        return None
    _write("review.json", rev.model_dump_json(indent=2))
    _write("review.md", review_markdown(rev))
    set_outputs(verdict=rev.verdict)
    return rev


def governance(product: str) -> GovernanceReport | None:
    ws, run_dir = checkout_workspace("governance")
    workspace.dbt(ws, "build", "--quiet")
    workspace.dbt(ws, "parse", "--quiet")
    _run("governance", ws, run_dir, {"product_id": product})
    try:
        rep = GovernanceReport.model_validate_json((ws / "output" / "governance.json").read_text())
    except Exception as exc:  # noqa: BLE001
        _write("governance.md", f"### ⚠️ Governance check failed\n\n```\n{str(exc)[:1500]}\n```\n")
        set_outputs(compliant="failed")
        return None
    _write("governance.json", rep.model_dump_json(indent=2))
    _write("governance.md", governance_markdown(rep))
    set_outputs(compliant=str(rep.compliant and not rep.violations).lower())
    return rep


def feedback(directory: Path | None = None) -> bool:
    """Merge checks, review and governance findings into ``feedback.md`` for a rework round."""
    src = directory or out_dir()
    items: list[str] = []
    if (src / "checks.json").exists():
        c = json.loads((src / "checks.json").read_text())
        items += [f"- [checks] {g['gate']}: {g['detail']}" for g in c["gates"] if not g["passed"]]
        items += [f"- [acceptance] {a['id']}: {a['detail']}" for a in c.get("acceptance", []) if not a["passed"]]
    if (src / "review.json").exists():
        r = Review.model_validate_json((src / "review.json").read_text())
        if r.verdict == "request_changes":
            items += [f"- [review/{f.severity}] {f.file}: {f.message}" + (f" (suggestion: {f.suggestion})" if f.suggestion else "")
                      for f in r.findings if f.severity in ("blocker", "major", "minor")]
    if (src / "governance.json").exists():
        g = GovernanceReport.model_validate_json((src / "governance.json").read_text())
        items += [f"- [governance/{v.rule_id}] {v.model}{'.' + v.column if v.column else ''}: {v.message}" for v in g.violations]
    _write("feedback.md", "# Findings to address\n\n" + "\n".join(items) + "\n" if items else "")
    set_outputs(has_findings=str(bool(items)).lower(), findings=len(items))
    return bool(items)


def line_manager(runs_dir: Path) -> LineManagerReport | None:
    ws, run_dir = checkout_workspace("line-manager")
    shutil.copytree(runs_dir, ws / "input" / "runs")
    shutil.copytree(paths.AGENTS, ws / "agents", ignore=shutil.ignore_patterns("__pycache__"))
    _run("line_manager", ws, run_dir)
    try:
        rep = LineManagerReport.model_validate_json((ws / "output" / "recommendations.json").read_text())
    except Exception as exc:  # noqa: BLE001
        _write("line_manager.md", f"Line manager failed: {exc}\n")
        return None
    report_md = (ws / "output" / "report.md").read_text() if (ws / "output" / "report.md").exists() else rep.summary
    recs = "\n".join(f"- **{r.target_agent}** — {r.pattern}\n  - evidence: {r.evidence}\n  - change: {r.change}"
                     + (f" (`{r.file}`)" if r.file else "") for r in rep.recommendations)
    _write("line_manager.md", f"{report_md}\n\n## Recommendations\n\n{recs}\n")
    return rep


def collect_runs(dest: Path) -> int:
    """Copy summaries + traces of every run (not the workspaces) into ``dest`` for upload."""
    n = 0
    for summary in paths.RUNS.rglob("summary.json"):
        if "workspace" in summary.parts:
            continue
        target = dest / summary.parent.relative_to(paths.RUNS)
        target.mkdir(parents=True, exist_ok=True)
        for f in ("summary.json", "trace.jsonl", "prompt.txt"):
            if (summary.parent / f).exists():
                shutil.copy(summary.parent / f, target / f)
        n += 1
    return n


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())
