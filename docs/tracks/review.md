# Track: Review agent

**Station.** Reviews the change on branch `feature` against `main`: are the numbers
right, does it match the spec, are tests and docs present and *true*? It can auto-approve.
Output: `output/review.json` (verdict, findings, docs_up_to_date).

```bash
factory run review --case review-02-fanout
factory bench run review --repeat 3
```

**Seed cases.** A clean PR (must be approved - false alarms stall the line), a fan-out bug,
a dropped QA-account filter that docs still claim, docs contradicting the code + removed
tests, and a hard-coded FX rate that passes every acceptance check.

**Ideas to improve**
- Working method: start from `git diff main...feature`, not from reading the repo.
- Run the numbers: `dbt build`, `factory accept input/spec.yaml`, and targeted SQL
  (e.g. compare totals with `fct_orders`). Two of the bugs move totals.
- A review checklist skill: fan-out joins, filters required by the business rules,
  hard-coded constants, docs-vs-code, removed tests.
- Calibrate the verdict: what is a blocker? When is approving right?
- Stretch: post the review on a real GitHub PR.

**Benchmark ideas.** A `left join` turned `inner join`; a ratio averaged instead of
ratio-of-sums; a PR whose description lies; a clean but large refactor (no false alarms).
