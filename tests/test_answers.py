"""answers.json: the template in the issue, the shape check and the grading."""

import json

from factory import answers, paths

ISSUE = """## Questions\n\n- **Q1** ...\n\n## Answers\n\n```json\n{"Q1": {"a": 0, "b": 0}, "Q2": 0}\n```\n"""


def test_template_and_shape():
    tpl = answers.template(ISSUE)
    assert tpl == {"Q1": {"a": 0, "b": 0}, "Q2": 0}
    assert answers.shape_problems({"Q1": {"a": 1, "b": 2.5}, "Q2": 3}, tpl) == []
    assert answers.shape_problems({"Q1": {"a": "x"}}, tpl) == ["Q1: key 'b' is missing", "Q1: 'a' is not a number",
                                                              "Q2 is missing"]
    assert answers.shape_problems([1], tpl) == ["answers.json is not a JSON object"]


def test_score():
    right = {"Q1": {"a": 100.0, "b": 200.0}, "Q2": 0.5}
    assert answers.score({"Q1": {"a": 100.4, "b": 300}, "Q2": 0.501}, right) == {"Q1": 0.5, "Q2": 1.0}
    assert answers.score(None, right) == {"Q1": 0.0, "Q2": 0.0}
    assert answers.score({"Q1": {"a": True, "b": 200}, "Q2": "0.5"}, right) == {"Q1": 0.5, "Q2": 0.0}


def test_practice_requests_have_a_template_their_answers_fit():
    for issue in paths.PRODUCTS.glob("*/issue.md"):
        right = issue.parent / "answers.json"
        if right.exists():
            tpl = answers.template(issue.read_text())
            assert tpl and answers.shape_problems(json.loads(right.read_text()), tpl) == [], issue
