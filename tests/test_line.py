"""The line with fake agents: hand-offs, the shape check, rework and scoring, without a model."""

import asyncio
import json
import shutil

from factory import competition, paths

FAKE = '''
import json, pathlib
TASK = "fake"

class Out:
    messages, metrics, status = [], None, "completed"

class Fake:
    model, tool_hooks = type("M", (), {{"id": "google/gemma-4-31b-it"}})(), []
    def __init__(self, ws): self.ws = pathlib.Path(ws)
    async def arun(self, task):
        {body}
        return Out()

def build(ws):
    return Fake(ws)
'''
INTAKE = 'self.ws.joinpath("output/spec.json").write_text(json.dumps({"status": "ready", "questions": []}))'
# first round: Q2 missing; after feedback: complete
IMPLEMENT = ('done = self.ws.joinpath("input/feedback.md").exists(); '
             'self.ws.joinpath("output/answers.json").write_text(json.dumps({"Q1": 1, **({"Q2": 2} if done else {})}))')
REVIEW = 'self.ws.joinpath("output/review.json").write_text(json.dumps({"verdict": "approve"}))'


def test_line_reworks_until_the_shape_is_right(tmp_path, monkeypatch):
    from factory.line import run_line

    for name, body in [("intake", INTAKE), ("implement", IMPLEMENT), ("review", REVIEW)]:
        (tmp_path / "agents" / name).mkdir(parents=True)
        (tmp_path / "agents" / name / "agent.py").write_text(FAKE.format(body=body))
    shutil.copy(paths.AGENTS / "line.yaml", tmp_path / "agents" / "line.yaml")
    issue = tmp_path / "issue.md"
    issue.write_text('## Answers\n\n```json\n{"Q1": 0, "Q2": 0}\n```\n')
    monkeypatch.setattr(paths, "RUNS", tmp_path / "runs")

    out = asyncio.run(run_line(issue, agents_dir=tmp_path / "agents"))
    assert out["outcome"] == "answered" and out["answers"] == {"Q1": 1, "Q2": 2}
    assert [s["stage"] for s in out["stations"]] == ["intake", "implement", "review", "implement", "review"]

    sub = competition.export_submission(tmp_path / "sub")
    right = tmp_path / "right.json"
    right.write_text(json.dumps({"Q1": 1, "Q2": 3}))
    s = competition.score(sub, right, duration_s=60, cost_usd=0.0)
    assert s["points"]["correctness"] == 35.0 and s["points"]["efficiency"] == 7.5
