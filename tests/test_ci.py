"""The CI stations (`factory ci ...`) end to end, with scripted agents instead of LLMs.

Mimics what .github/workflows/factory-build.yml and factory-pr.yml do, on a temp
copy of the repo: intake -> branch -> implement (with a planted bug) -> bi ->
checks fail -> review + governance -> feedback -> rework -> everything green.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from factory import ci, paths, runner, workspace

GOLDEN = paths.PRODUCTS / "category_performance"
pytestmark = pytest.mark.skipif(not paths.WAREHOUSE_DB.exists(), reason="run `factory setup` first")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    shutil.copytree(paths.WAREHOUSE, root / "warehouse", ignore=shutil.ignore_patterns("target", "logs", "renders"))
    shutil.copytree(paths.STANDARDS, root / "standards")
    git(root, "init", "-q", "-b", "main")
    (root / ".gitignore").write_text("warehouse/*.duckdb\nwarehouse/target/\nfactory-out/\nruns/\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "main")
    monkeypatch.setattr(paths, "ROOT", root)
    monkeypatch.setattr(paths, "WAREHOUSE", root / "warehouse")
    monkeypatch.setattr(paths, "WAREHOUSE_DB", root / "warehouse" / "warehouse.duckdb")
    monkeypatch.setattr(paths, "STANDARDS", root / "standards")
    monkeypatch.setattr(paths, "RUNS", root / "runs")
    monkeypatch.setenv("FACTORY_OUT", str(root / "factory-out"))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "gh_output"))
    return root


def outputs(tmp_path: Path) -> dict[str, str]:
    lines = (tmp_path / "gh_output").read_text().splitlines()
    return dict(line.split("=", 1) for line in lines)


def script_agents(monkeypatch, log: list):
    """Replace the LLM agents with scripts that write golden (or deliberately broken) outputs."""

    def fake(agent_dir, ws, run_dir, ctx=None, meta=None):
        stage = Path(agent_dir).name
        log.append(stage)
        product = "category_performance"
        if stage == "intake":
            shutil.copy(GOLDEN / "spec.yaml", ws / "output" / "spec.yaml")
        elif stage == "implement":
            workspace.install_product(ws, product, board=False)
            if not (ws / "input" / "feedback.md").exists():  # first attempt has the fan-out bug
                workspace.overlay(ws, paths.BENCHMARK / "fixtures" / "review" / "fanout")
        elif stage == "bi":
            assert (ws / "warehouse" / "models" / "marts" / product).exists(), "bi must see the branch's models"
            shutil.copy(GOLDEN / "board.yml", ws / "warehouse" / "charts" / f"{product}.yml")
        elif stage == "review":
            diff = subprocess.run(["git", "diff", "--stat", "main...feature"], cwd=ws, capture_output=True, text=True).stdout
            assert "fct_category_revenue_monthly.sql" in diff, diff
            buggy = "o.net_amount_eur" in (ws / "warehouse/models/marts" / product / "fct_category_revenue_monthly.sql").read_text()
            review = {"verdict": "request_changes" if buggy else "approve", "summary": "s", "docs_up_to_date": True,
                      "findings": [{"severity": "blocker", "category": "correctness",
                                    "file": f"warehouse/models/marts/{product}/fct_category_revenue_monthly.sql",
                                    "message": "fan-out: order-level amount summed per line"}] if buggy else []}
            (ws / "output" / "review.json").write_text(json.dumps(review))
        elif stage == "governance":
            (ws / "output" / "governance.json").write_text(json.dumps({"product_id": product, "compliant": True}))
        (run_dir / "summary.json").write_text("{}")
        return {"status": "ok", "total_cost_usd": 0.0, "num_turns": 1, "final_text": f"{stage} done"}

    monkeypatch.setattr(runner, "run_agent_sync", fake)


def test_ci_pipeline_with_rework(repo, tmp_path, monkeypatch):
    log: list[str] = []
    script_agents(monkeypatch, log)
    out = repo / "factory-out"
    spec = Path("warehouse/specs/category_performance.yaml")
    monkeypatch.chdir(repo)

    # factory-build.yml
    issue = tmp_path / "issue.md"
    shutil.copy(GOLDEN / "issue.md", issue)
    ci.intake(issue)
    assert outputs(tmp_path)["status"] == "ready"
    assert (repo / spec).exists() and "Business questions" in (out / "comment.md").read_text()
    git(repo, "checkout", "-q", "-b", "factory/issue-101")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "spec")

    ci.implement(repo / spec)
    ci.bi(repo / spec)
    assert (repo / "warehouse/charts/category_performance.yml").exists()
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "implement + bi")

    # factory-pr.yml, round 1: the planted bug is caught
    assert ci.checks(repo / spec) is False
    assert ci.review(repo / spec, "main").verdict == "request_changes"
    assert ci.governance("category_performance").compliant
    assert ci.feedback() is True
    fb = (out / "feedback.md").read_text()
    assert "[acceptance]" in fb and "[review/blocker]" in fb

    # rework round
    ci.implement(repo / spec, out / "feedback.md")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "factory: rework round 1")
    for f in ("checks.json", "review.json", "governance.json", "feedback.md"):
        (out / f).unlink()

    # factory-pr.yml, round 2: all green
    assert ci.checks(repo / spec) is True, (out / "checks.md").read_text()
    assert ci.review(repo / spec, "main").verdict == "approve"
    assert ci.governance("category_performance").compliant
    assert ci.feedback() is False
    assert log == ["intake", "implement", "bi", "review", "governance", "implement", "review", "governance"]

    collected = ci.collect_runs(tmp_path / "traces")
    assert collected == 8
    assert not list((tmp_path / "traces").rglob("*.duckdb"))


def test_ci_intake_needs_clarification(repo, tmp_path, monkeypatch):
    def fake(agent_dir, ws, run_dir, ctx=None, meta=None):
        shutil.copy(paths.PRODUCTS / "store_performance" / "oracle_spec.yaml", ws / "output" / "spec.yaml")
        return {"status": "ok", "total_cost_usd": 0.0, "num_turns": 1}

    monkeypatch.setattr(runner, "run_agent_sync", fake)
    ci.intake(paths.PRODUCTS / "store_performance" / "issue.md")
    assert outputs(tmp_path)["status"] == "needs_clarification"
    comment = (repo / "factory-out" / "comment.md").read_text()
    assert "Questions for you" in comment and "footfall" in comment
    assert not (repo / "warehouse" / "specs").exists()


def test_workflows_are_valid_yaml():
    import yaml

    wf = Path(__file__).resolve().parents[1] / ".github" / "workflows"
    names = sorted(p.name for p in wf.glob("*.yml"))
    assert names == ["ci.yml", "factory-bench.yml", "factory-build.yml", "factory-line-manager.yml", "factory-pr.yml"]
    for p in wf.glob("*.yml"):
        doc = yaml.safe_load(p.read_text())
        assert doc["jobs"] and (True in doc or "on" in doc), p  # PyYAML parses `on:` as True
