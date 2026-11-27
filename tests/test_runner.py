"""The workspace guard and the base agent's tools."""

import asyncio

import pytest

from factory import paths
from factory.runner import _escapes

WS = paths.RUNS / "x" / "workspace"


@pytest.mark.parametrize("tool,args,escapes", [
    ("read_file", {"file_name": "data/orders.csv"}, False),
    ("read_file", {"file_name": str(WS / "output/spec.json")}, False),
    ("read_file", {"file_name": str(paths.ROOT / "benchmark/products/a/answers.json")}, True),
    ("list_files", {"directory": "../.."}, True),
    ("shell", {"command": "python output/analysis.py"}, False),
    ("shell", {"command": f"cd {WS} && python output/analysis.py"}, False),
    ("shell", {"command": f"{paths.ROOT}/.venv/bin/python output/analysis.py"}, False),
    ("shell", {"command": "select 1 -- a..b"}, False),
    ("shell", {"command": f"cd {paths.ROOT} && cat benchmark/products/x/answers.json"}, True),
    ("shell", {"command": "cat ../../benchmark/products/x/answers.json"}, True),
    ("shell", {"command": f"ls {paths.ROOT}-oracle"}, True),
    ("shell", {"command": "ls ~/anything"}, True),
    ("shell", {"command": "cd && ls"}, True),
])
def test_workspace_guard(tool, args, escapes):
    assert (_escapes(WS, tool, args) is not None) == escapes


def test_guard_hook_shell_and_sql(tmp_path):
    from factory.agent import shell_tool, sql_tool
    from factory.runner import workspace_guard

    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "t.csv").write_text("a,b\n1,2\n3,4\n")
    shell, guard = shell_tool(tmp_path), workspace_guard(tmp_path)
    out = asyncio.run(guard("shell", shell, {"command": "pwd && echo hi > f.txt"}))
    assert out.startswith("exit 0") and str(tmp_path.resolve()) in out and (tmp_path / "f.txt").exists()
    assert asyncio.run(guard("shell", shell, {"command": "cat ../../secret"})).startswith("Denied")
    assert sql_tool(tmp_path)("select sum(b) as s from t") == "s\n6"
    assert sql_tool(tmp_path)("select nope from t").startswith("error")


def test_baseline_agents_build(monkeypatch, tmp_path):
    """Every station in agents/line.yaml has an agent.py with TASK and build() returning an Agno agent."""
    from factory.line import config
    from factory.runner import load

    monkeypatch.setenv("LLM_API_KEY", "test")
    for s in config()["stations"]:
        mod = load(paths.AGENTS / s)
        assert mod.TASK.strip()
        assert mod.build(tmp_path).tools


def test_sql_cannot_read_outside_data(tmp_path):
    from factory.agent import sql_tool

    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "t.csv").write_text("a\n1\n")
    run_sql = sql_tool(tmp_path)
    assert run_sql("select count(*) as n from t") == "n\n1"
    for q in ["select * from read_json_auto('benchmark/products/category_performance/answers.json')",
              f"select * from read_csv_auto('{paths.ROOT}/benchmark/products/category_performance/answers.json')",
              "set enable_external_access = true"]:
        assert run_sql(q).startswith("error"), q


def test_base_agent_with_a_skill(monkeypatch, tmp_path):
    from factory.agent import base_agent

    monkeypatch.setenv("LLM_API_KEY", "test")
    skill = tmp_path / "skills" / "fernhill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: fernhill\ndescription: Fernhill's rules\n---\n\nRevenue = shipped.\n")
    agent = base_agent(tmp_path, "You are an analyst.", skills=[skill], effort="low", model="qwen/qwen4-max")
    assert agent.skills is not None and agent.model.id == "qwen/qwen4-max"
