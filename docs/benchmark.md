# The benchmark

```bash
factory bench run <station> [--case <id>] [--repeat 3] [--agent agents/<x>] [--label v2]
factory bench run <station> --oracle      # grade the right answers: always 1.0
factory bench report [--stage <station>]  # every recorded run, best first
factory bench check benchmark/cases/<station>/<case>.yaml   # is my case valid?
```

Each run creates `runs/bench-<time>-<station>-<label>/<case>-r<n>/` with the workspace, the task,
the trace and `summary.json` with every grade. With Phoenix running, every run is also a trace at
http://localhost:6006, one session per benchmark run.

## A case

A YAML file in `benchmark/cases/<station>/`, readable on its own:

```yaml
id: review-03-no-fx
stage: review
description: GBP orders are summed as if they were euro.
input:                                   # what goes into the workspace
  issue: products/category_performance/issue.md
  spec: products/category_performance/spec.json
  work: fixtures/review/no_fx            # answers.json and the code under review
expected:                                # what the grader checks
  verdict: request_changes
  defects:
    - {id: currency, any: [gbp, fx, exchange rate, currency, pound]}
```

Paths resolve next to the case file first, then in `benchmark/`. Keep the files your own cases need
next to them under `benchmark/cases/`: that folder is what the final takes from your fork.

| Station | Input | Graded on (weight) |
|---|---|---|
| intake | a request | the status: ready, needs clarification or infeasible (2); every question in the spec (1); each rule the definitions must mention (1 each) |
| implement | a request and a right spec | per question, the share of values within 0.5% of the right answer (1 each) |
| review | a request, a spec, answers and the code | the verdict (2); each planted bug named in a finding (1 each) |

A case is **valid** when doing nothing scores 0 and the right answer scores 1: `factory bench check`
tests that, `pytest` tests it for every case, and the final counts your valid new cases.

## Writing your own cases

Good cases come from failures you saw in the traces.

- **Same rule, new question.** A request about another table with the same trap (test accounts, GBP,
  placed orders) tells you whether the agent learnt the rule or the case.
- **Clean controls.** For every "find the bug" case, have a clean one. Otherwise an agent that
  always requests changes wins.
- **An implement case needs right answers.** Compute them with a script you trust, and check the
  numbers by hand on a few rows.

## The whole line

Station cases grade one agent on clean inputs. The final grades the whole line on one request.
Practise that on a public request:

```bash
factory line --issue benchmark/products/customer_retention/issue.md
factory score runs/<the line run>
```

## Keyword graders

The intake and review graders look for words. An agent can name the bug in words the list doesn't
have, or use a word without understanding. Read the `detail` of a low grade before you believe it.

## Noise, cost and repeats

Agents are not deterministic. One run tells you almost nothing: use `--repeat 3` and look at the
spread before you call something better. Watch cost and turns next to the score.
