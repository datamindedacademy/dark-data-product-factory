"""The final-challenge scoring (factory/competition.py), end to end without LLMs.

A golden product must score full marks on everything the oracle grades, a planted bug must cost
correctness points, an empty submission must score 0, and nothing but SQL/YAML may reach the build.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from factory import competition, paths

PRODUCT = "category_performance"
GOLDEN = paths.PRODUCTS / PRODUCT
ORACLE = GOLDEN / "spec.yaml"
pytestmark = pytest.mark.skipif(not paths.WAREHOUSE_DB.exists(), reason="run `factory setup` first")


def submission(tmp_path: Path, overlay: Path | None = None, cost: float | None = 1.0) -> Path:
    sub = tmp_path / "submission"
    shutil.copytree(GOLDEN / "models", sub / "models")
    shutil.copy(GOLDEN / "spec.yaml", sub / "spec.yaml")
    shutil.copy(GOLDEN / "board.yml", sub / "board.yml")
    if overlay:
        shutil.copytree(overlay / "warehouse" / "models" / "marts" / PRODUCT, sub / "models", dirs_exist_ok=True)
    (sub / "traces" / "implement-1").mkdir(parents=True)
    (sub / "traces" / "implement-1" / "summary.json").write_text(
        json.dumps({"stage": "implement", "framework": "agno", "total_cost_usd": cost}))
    return sub


def test_golden_product_scores_full_marks(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS", tmp_path / "runs")
    sub = submission(tmp_path)
    (sub / "models" / "evil.py").write_text("raise SystemExit('team code must never run in the build job')")
    build = competition.build_submission(sub, tmp_path / "build")
    assert build["dbt_build"] and build["models"] == 1, build
    case = paths.CASES / "review" / "review-02-fanout.yaml"
    (tmp_path / "build" / "cases.json").write_text(json.dumps({str(case): competition.valid_case(case)}))
    s = competition.score(sub, tmp_path / "build", ORACLE, paths.WAREHOUSE_DB, duration_s=300)
    assert s["points"] | {"benchmark": 0} == competition.POINTS | {"benchmark": 0}, s["detail"]
    assert s["points"]["benchmark"] == pytest.approx(10 / 3, abs=0.1)  # one valid case of the three needed
    assert s["agno_stations"] == ["implement"]
    assert s["total"] == pytest.approx(100 - 10 * 2 / 3, abs=0.2)
    assert f"| correctness | {competition.POINTS['correctness']} / {competition.POINTS['correctness']} |" in competition.score_markdown("team", s)


def test_planted_bug_and_unreported_cost_lose_points(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS", tmp_path / "runs")
    sub = submission(tmp_path, overlay=paths.BENCHMARK / "fixtures" / "review" / "fanout", cost=None)
    competition.build_submission(sub, tmp_path / "build")
    s = competition.score(sub, tmp_path / "build", ORACLE, paths.WAREHOUSE_DB, duration_s=300)
    assert 0 < s["points"]["correctness"] < competition.POINTS["correctness"], s["detail"]
    assert s["points"]["interface"] == competition.POINTS["interface"]
    assert s["cost_usd"] is None and s["points"]["efficiency"] < competition.POINTS["efficiency"] / 2


def test_empty_submission_scores_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS", tmp_path / "runs")
    sub = tmp_path / "submission"
    sub.mkdir()
    build = competition.build_submission(sub, tmp_path / "build")
    assert "error" in build
    assert competition.score(sub, tmp_path / "build", ORACLE, paths.WAREHOUSE_DB)["total"] == 0


def test_final_issue_publishes_the_interface_not_the_checks():
    text = competition.final_issue(GOLDEN / "issue.md", ORACLE)
    assert "fct_category_revenue_monthly" in text and "net_revenue_eur" in text and "**Q3**" in text
    assert "reference_sql" not in text and "fernhill.test" not in text



def test_checkup_scores_the_judgement_rules(tmp_path):
    from factory.tools.checkup import check

    model = {"resource_type": "model", "name": "fct_x", "unique_id": "model.f.fct_x", "fqn": ["f", "marts", "prod", "fct_x"],
             "columns": {"customer_email": {}, "margin_pct": {}, "revenue": {}, "net_revenue_eur": {}},
             "config": {}, "depends_on": {"nodes": []}}
    (tmp_path / "prod.yml").write_text("queries:\n  a: {sql: select 1 from main.fct_x}\n")
    found = {(f.rule_id, f.column) for f in check({"nodes": {"m": model}}, "prod", tmp_path)}
    assert {("GOV-006", "customer_email"), ("GOV-008", "margin_pct"), ("GOV-008", "revenue"), ("GOV-010", None)} <= found
    assert ("GOV-008", "net_revenue_eur") not in found


def test_a_chart_of_a_wrong_number_does_not_answer_the_question(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS", tmp_path / "runs")
    sub = submission(tmp_path, overlay=paths.BENCHMARK / "fixtures" / "review" / "fanout")
    competition.build_submission(sub, tmp_path / "build")
    s = competition.score(sub, tmp_path / "build", ORACLE, paths.WAREHOUSE_DB, duration_s=300)
    assert s["points"]["dashboard"] < competition.POINTS["dashboard"], s["detail"]
