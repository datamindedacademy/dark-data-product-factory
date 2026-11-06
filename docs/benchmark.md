# The benchmark

```bash
factory bench list
factory bench run <station> [--case <id>] [--repeat 3] [--agent-dir agents/<x>] [--judge] [--label v2]
factory bench run <station> --oracle      # grade the golden outputs: must be 1.0
factory bench report [--stage <station>]  # every recorded run, best first
factory run <station> --case <id>         # one run, grades printed, workspace kept for inspection
```

Each run creates `runs/bench-<time>-<station>-<label>/<case>-r<n>/` with the workspace,
the prompt, the trace and `summary.json` (including every grade and its detail). The
aggregate goes to `benchmark/results/<bench-dir>.json`, which `bench report` reads.

## How a case works

A case is a YAML file in `benchmark/cases/<station>/`:

```yaml
id: review-02-fanout
stage: review
description: Order-level net amount is summed once per order line.
input:                      # what setup() puts in the workspace
  product: category_performance
  spec: products/category_performance/spec.yaml
  pr: fixtures/review/prs/category_performance.md
  overlay: fixtures/review/fanout           # files copied over the golden product on branch feature
expected:                   # what grade() compares against
  verdict: request_changes
  defects:
    - id: fanout
      file: warehouse/models/marts/category_performance/fct_category_revenue_monthly.sql
      keywords: [fan-out, duplicat, double count, inflat, order-level, ...]
```

Paths resolve relative to the case file, then to `benchmark/`. Each station
(`benchmark/stages/<station>.py`) implements `setup` (build the workspace), `oracle`
(write the golden output) and `grade` (return weighted `Grade`s). The case score is the
weighted mean; the station score is the mean over cases.

## What each station is graded on

| Station | Graders (weight) |
|---|---|
| intake | spec valid (1), status ready / needs_clarification / infeasible (3), data traps found (3), question coverage (2), grounding: inputs exist and reference SQL runs (2), acceptance checks per question (2) or blocker explained (2); `--judge`: rubric (3) |
| implement | dbt build (2), outputs match spec (2), visible acceptance checks (4), **hidden** acceptance checks (3), Fernhill checkup metrics clean (2) |
| review | verdict (4), planted defect recall (3) or no false alarms on a clean PR (2), docs flag (1) |
| governance | violation F1 on (rule, model) (5), recall on rules that need judgement (3), compliant flag (1) |
| bi | `dct validate` (2), `dct render` (2), question coverage via query `notes` (3), reads product models (1); `--judge`: answers the questions (3) |
| line manager | planted pattern recall (5), recommendations point at real files (1), focus (1); `--judge`: rubric (2) |

Doing nothing scores 0 on every case and the golden answer scores 1.0; `pytest` checks
both, and checks that the planted defects really break the numbers.

## Designing your own cases

Good cases come from failures you saw in traces, not from imagination. Some patterns:

- **Adversarial input.** An issue that sounds clear but asks for data that does not exist;
  a PR whose description claims tests that were removed; a governance case where the
  checkup is green but a human would object.
- **Same skill, new surface.** A different product with the same trap (QA accounts,
  GBP, cancellations) tells you whether the agent learned the rule or the case.
- **Clean controls.** For every "find the bug" case, have a clean one. Otherwise an
  agent that always says "request changes" wins.
- **Hidden checks.** The implement cases hide some acceptance checks from the agent
  (`expected.hidden_checks`). Passing visible but failing hidden checks = overfitting.

To add a new data product, create `benchmark/products/<id>/` with `issue.md`,
`spec.yaml`, `models/` and `board.yml`; `pytest -q -k golden` checks they agree.
Then any station can reuse it.

## Keyword graders vs. LLM judges

Most graders here are deterministic: cheap, fast and repeatable. Some (defect recall,
data traps, line-manager patterns) use keyword lists. They are crude: an agent can find the
bug and describe it in words the list does not contain (false negative), or mention a
keyword without understanding (false positive). Read the `detail` of low grades before
you believe them.

`--judge` adds LLM-as-judge graders (`factory/judge.py`, rubric with 1-5 per criterion).
Before trusting a judge, calibrate it:

1. Score the golden output (`--oracle --judge`): it should be near the top.
2. Score a deliberately bad output (e.g. a spec without acceptance checks): it should be
   clearly lower.
3. Run the same input 3 times: the spread tells you the judge's own noise.

Replacing a keyword grader with a calibrated judge (or the other way around) is a valid
benchmark contribution.

## Noise, cost and repeats

Agents are not deterministic. One run tells you almost nothing; use `--repeat 3` at least
and look at the stdev before claiming an improvement. Track cost and turns next to the
score: an agent that scores +0.02 at twice the cost is usually not better. Use
`--case` to iterate on one failing case cheaply, then confirm on the full set.
