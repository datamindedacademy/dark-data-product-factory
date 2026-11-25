"""Checks on the benchmark itself. No LLM calls - run these after changing cases or graders.

    pytest -q                 # ~4 minutes, needs `factory setup` first
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core import load_cases, weighted
from benchmark.harness import STAGES
from factory import paths, workspace
from factory.acceptance import run_acceptance
from factory.contracts import DataProductSpec
from factory.runner import AgentConfig, default_agent
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
        found = {(v["rule_id"], v["model"]) for v in checkup.run(
            ws / "warehouse", case.input["product"], checkup.MECHANICAL_RULES + checkup.JUDGEMENT_RULES)["violations"]}
        expected = {(v["rule_id"], v["model"]) for v in case.expected["violations"] if v["rule_id"] != "GOV-011"}
        assert found == expected, f"{case.id} with the judgement heuristics (what the final grades)"


@pytest.mark.parametrize("agent", sorted(p.name for p in paths.AGENTS.iterdir() if (p / "agent.yaml").exists()))
def test_agent_configs_build(agent, tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-or-test")  # building an agent makes no call
    cfg = AgentConfig.load(paths.AGENTS / agent)
    ws = _ws(tmp_path)
    assert (cfg.dir / cfg.prompt).exists()
    if (cfg.dir / "agent.py").exists():  # the team builds it
        from factory.runner import _load

        assert hasattr(_load(cfg.dir / "agent.py").build_agent(ws, cfg), "arun")
        return
    agent = default_agent(ws, cfg)
    names = {getattr(t, "__name__", None) or type(t).__name__ for t in agent.tools}
    if "Bash" in cfg.builtin_tools:
        assert "bash" in names
    for tool in (cfg.mcp or {}).get("warehouse") or []:
        assert tool in names  # the prompts name run_sql
    if (cfg.mcp or {}).get("governance"):
        assert "checkup" in names


def test_e2e_line_with_scripted_agents(tmp_path, monkeypatch):
    """Runs the full orchestration with fake agents that write golden outputs (no LLM)."""
    import asyncio
    import json
    import shutil

    from factory import e2e

    product = "category_performance"
    golden = paths.PRODUCTS / product
    calls, events, workspaces = [], [], {}

    async def fake_run_agent(agent_dir, ws, run_dir, ctx=None, meta=None):
        stage = Path(agent_dir).name
        calls.append(stage)
        workspaces[stage] = ws
        events.append(f"start {stage}")
        await asyncio.sleep(0)
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
        events.append(f"end {stage}")
        return {"status": "ok", "total_cost_usd": 0.0, "num_turns": 1, "duration_ms": 1, "final_text": "done"}

    monkeypatch.setattr(e2e, "run_agent", fake_run_agent)
    monkeypatch.setattr(paths, "RUNS", tmp_path)
    summary = asyncio.run(e2e.run_line(golden / "issue.md"))
    assert calls == ["intake", "implement", "review", "governance", "bi"]
    assert summary["outcome"] == "delivered", summary
    assert summary["acceptance"] == 1.0
    # review and governance overlap, each in its own workspace
    assert events.index("start governance") < events.index("end review")
    assert workspaces["governance"] != workspaces["review"]

    from factory import competition

    sub = competition.export_submission(tmp_path.with_name(tmp_path.name + "-submission"))
    assert {p.name for p in sub.iterdir()} >= {"spec.yaml", "models", "board.yml", "e2e_summary.json"}


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


def test_agno_run_becomes_a_trace(tmp_path):
    """An agent dir with agent.py: its RunOutput becomes the trace and the summary."""
    import asyncio
    import json

    from factory.runner import run_agent

    agent = tmp_path / "fake-agno"
    agent.mkdir()
    (agent / "agent.yaml").write_text("model: google/gemma-4-31b-it\noutputs: [output/x.txt]\n")
    (agent / "system_prompt.md").write_text("sys")
    (agent / "prompt.md").write_text("work in $workspace")
    (agent / "agent.py").write_text('''
from agno.metrics import RunMetrics
from agno.models.message import Message
from agno.run.agent import RunOutput
from agno.run.base import RunStatus

class Fake:
    async def arun(self, prompt):
        assert "$workspace" not in prompt
        return RunOutput(content="done", status=RunStatus.completed,
                         metrics=RunMetrics(input_tokens=1_000_000, output_tokens=100_000, cost=0.42),
                         messages=[Message(role="user", content=prompt), Message(role="assistant", content="querying"),
                                   Message(role="tool", tool_name="run_sql", tool_args={"sql": "select 1"}, tool_call_id="t1",
                                           content="boom", tool_call_error=True),
                                   Message(role="assistant", content="done")])

def build_agent(ws, cfg):
    return Fake()
''')
    ws, run_dir = tmp_path / "ws", tmp_path / "run"
    ws.mkdir()
    run_dir.mkdir()
    summary = asyncio.run(run_agent(agent, ws, run_dir))
    assert summary["framework"] == "agno" and summary["status"] == "ok" and summary["num_turns"] == 2
    assert summary["tool_calls"] == {"run_sql": 1} and summary["tool_errors"] == {"run_sql": 1}
    assert summary["total_cost_usd"] == 0.42  # what OpenRouter reported
    assert summary["final_text"] == "done" and summary["missing_outputs"] == ["output/x.txt"]
    events = [json.loads(line)["type"] for line in (tmp_path / "run" / "trace.jsonl").read_text().splitlines()]
    assert events == ["assistant_text", "tool_use", "tool_result", "assistant_text", "result"]
