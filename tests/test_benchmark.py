"""Checks on the benchmark itself. No LLM calls - run these after changing cases or graders.

    pytest -q                 # ~2 minutes, needs `factory setup` first
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core import load_cases, weighted
from benchmark.harness import STAGES
from factory import paths, workspace
from factory.acceptance import run_acceptance
from factory.contracts import DataProductSpec
from factory.runner import AgentConfig, build_options
from factory.tools import checkup

ALL_CASES = [(s, c) for s in STAGES for c in load_cases(s)]
IDS = [c.id for _, c in ALL_CASES]

pytestmark = pytest.mark.skipif(not paths.WAREHOUSE_DB.exists(), reason="run `factory setup` first")


def _ws(tmp_path: Path) -> Path:
    return workspace.create(tmp_path / "run")


@pytest.mark.parametrize(("stage", "case"), ALL_CASES, ids=IDS)
def test_oracle_scores_perfect(stage, case, tmp_path):
    ws = _ws(tmp_path)
    STAGES[stage].setup(case, ws)
    STAGES[stage].oracle(case, ws)
    grades = STAGES[stage].grade(case, ws)
    assert weighted(grades) >= 0.99, [g for g in grades if g.score < 1]


@pytest.mark.parametrize(("stage", "case"), ALL_CASES, ids=IDS)
def test_doing_nothing_scores_zero(stage, case, tmp_path):
    ws = _ws(tmp_path)
    STAGES[stage].setup(case, ws)
    assert weighted(STAGES[stage].grade(case, ws)) == 0


@pytest.mark.parametrize("product", ["category_performance", "marketing_performance", "customer_retention"])
def test_golden_specs_pass_their_own_acceptance(product, tmp_path):
    ws = _ws(tmp_path)
    workspace.install_product(ws, product)
    assert workspace.dbt(ws, "build", "--quiet").returncode == 0
    report = run_acceptance(DataProductSpec.load(paths.PRODUCTS / product / "spec.yaml"), ws / "warehouse" / "warehouse.duckdb")
    assert report.passed == report.total, report.as_text()
    assert workspace.dct(ws, "validate", f"charts/{product}.yml").returncode == 0


@pytest.mark.parametrize(("case_id", "should_fail"), [
    ("review-01-clean", False), ("review-02-fanout", True), ("review-03-qa-accounts", True)])
def test_planted_defects_break_acceptance(case_id, should_fail, tmp_path):
    case = next(c for c in load_cases("review") if c.id == case_id)
    ws = _ws(tmp_path)
    STAGES["review"].setup(case, ws)
    report = run_acceptance(DataProductSpec.load(ws / "input" / "spec.yaml"), ws / "warehouse" / "warehouse.duckdb")
    assert (report.passed < report.total) == should_fail, report.as_text()


def test_checkup_finds_exactly_the_mechanical_violations(tmp_path):
    for case in load_cases("governance"):
        ws = workspace.create(tmp_path / case.id)
        STAGES["governance"].setup(case, ws)
        found = {(v["rule_id"], v["model"]) for v in checkup.run(ws / "warehouse", case.input["product"])["violations"]}
        expected = {(v["rule_id"], v["model"]) for v in case.expected["violations"]
                    if v["rule_id"] in checkup.MECHANICAL_RULES}
        assert found == expected, case.id


@pytest.mark.parametrize("agent", sorted(p.name for p in paths.AGENTS.iterdir() if (p / "agent.yaml").exists()))
def test_agent_configs_build(agent, tmp_path):
    cfg = AgentConfig.load(paths.AGENTS / agent)
    ws = _ws(tmp_path)
    workspace.install_agent_context(ws, cfg.dir, cfg.skills)
    opts = build_options(cfg, ws)
    assert opts.cwd == str(ws)
    assert (cfg.dir / cfg.prompt).exists()


def test_e2e_line_with_scripted_agents(tmp_path, monkeypatch):
    """Runs the full orchestration with fake agents that write golden outputs (no LLM)."""
    import asyncio
    import json
    import shutil

    from factory import e2e

    product = "category_performance"
    golden = paths.PRODUCTS / product
    calls = []

    async def fake_run_agent(agent_dir, ws, run_dir, ctx=None, meta=None):
        stage = Path(agent_dir).name
        calls.append(stage)
        if stage == "intake":
            shutil.copy(golden / "spec.yaml", ws / "output" / "spec.yaml")
        elif stage == "implement":
            workspace.install_product(ws, product, board=False)
            workspace.dbt(ws, "build", "--quiet")
        elif stage == "review":
            (ws / "output" / "review.json").write_text(json.dumps(
                {"verdict": "approve", "summary": "ok", "docs_up_to_date": True, "findings": []}))
        elif stage == "governance":
            (ws / "output" / "governance.json").write_text(json.dumps(
                {"product_id": product, "compliant": True, "violations": []}))
        elif stage == "bi":
            shutil.copy(golden / "board.yml", ws / "warehouse" / "charts" / f"{product}.yml")
        return {"status": "ok", "total_cost_usd": 0.0, "num_turns": 1, "duration_ms": 1, "final_text": "done"}

    monkeypatch.setattr(e2e, "run_agent", fake_run_agent)
    monkeypatch.setattr(paths, "RUNS", tmp_path)
    summary = asyncio.run(e2e.run_line(golden / "issue.md"))
    assert calls == ["intake", "implement", "review", "governance", "bi"]
    assert summary["outcome"] == "delivered", summary
    assert summary["acceptance"] == 1.0


def test_tracer_records_tools_and_cost(tmp_path):
    import json

    from claude_agent_sdk import (AssistantMessage, ResultMessage, SystemMessage, TextBlock, ToolResultBlock,
                                  ToolUseBlock, UserMessage)

    from factory.tracing import Tracer

    t = Tracer(tmp_path, {"agent": "x"})
    t.on_message(SystemMessage(subtype="init", data={"model": "m", "tools": ["Bash"], "skills": []}))
    t.on_message(AssistantMessage(content=[TextBlock(text="hi"), ToolUseBlock(id="1", name="Bash", input={"command": "ls"})],
                                  model="m"))
    t.on_message(UserMessage(content=[ToolResultBlock(tool_use_id="1", content="boom", is_error=True)]))
    t.on_message(ResultMessage(subtype="success", duration_ms=10, duration_api_ms=5, is_error=False, num_turns=1,
                               session_id="s", total_cost_usd=0.12, usage={"input_tokens": 5, "output_tokens": 7}))
    s = t.close()
    assert s["tool_calls"] == {"Bash": 1} and s["tool_errors"] == {"Bash": 1}
    assert s["total_cost_usd"] == 0.12 and s["status"] == "ok"
    types = [json.loads(line)["type"] for line in (tmp_path / "trace.jsonl").read_text().splitlines()]
    assert types == ["init", "assistant_text", "tool_use", "tool_result", "result"]


def test_checkup_tool_runs_real_checkup(tmp_path):
    """The governance agent's tool shells out to `checkup run` with the Fernhill plugin."""
    case = next(c for c in load_cases("governance") if c.id == "governance-02-mechanical")
    ws = _ws(tmp_path)
    STAGES["governance"].setup(case, ws)
    res = checkup.checkup_cli(ws / "warehouse", "marketing_performance")
    assert res.returncode == 0, res.stderr
    assert "GOV-005: fct_marketing_channel_daily" in res.stdout
    assert "GOV-009: fct_marketing_channel_daily" in res.stdout
    assert "fernhill_gov001_mart_naming" in res.stdout
