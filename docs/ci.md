# The factory as a CI pipeline

In production the factory runs as GitHub Actions, triggered by GitHub events. Nobody runs
anything by hand: an issue goes in, and a reviewed, governed, tested data product with a
dashboard is merged.

```
 issue labelled data-product-request
   │
   ▼  factory-build.yml
 intake ──not ready──▶ questions posted on the issue, label needs-clarification
   │                     └─ requester replies ─▶ intake runs again with the whole thread
   ready
   ▼
 branch factory/issue-<n>: warehouse/specs/<id>.yaml
   ▼
 implement ─▶ warehouse/models/marts/<id>/        (push)
   ▼
 bi        ─▶ warehouse/charts/<id>.yml           (push)
   ▼
 pull request "Closes #<n>", label factory
   │
   ▼  factory-pr.yml (every push to the PR)
 ┌ checks      dbt build · acceptance checks · checkup · dct validate   (no LLM)
 ├ review      review agent ─▶ PR review (approve / request changes)
 └ governance  governance agent ─▶ PR comment
   ▼
 decide ── all green ─────────────▶ label factory:approved, auto-merge (vars.FACTORY_AUTO_MERGE)
        ├─ findings, rounds left ─▶ implement agent reworks with feedback.md, pushes ─▶ factory-pr.yml again
        ├─ findings, no rounds ───▶ label needs-human
        └─ a gate did not report ─▶ label needs-human (a crashed agent never counts as green)

 factory-line-manager.yml (Mondays): last week's traces ─▶ line manager ─▶ issue with recommendations
 factory-bench.yml (label run-benchmark on a PR changing agents/): benchmark the changed stations
 ci.yml: pytest + oracle runs - CI for the factory code itself, no API key needed
 competition.yml (dispatched by the organisers): one team's line on one request, built and scored
```

`competition.yml` is the pipeline of the final challenge. It runs the laptop line (`factory e2e`)
in one job and scores the result in two more: see [competition.md](competition.md).

Two things differ between the issue → PR pipeline and the local `factory e2e` line. BI runs before review here, so the
review and the gates cover the dashboard too. And the rework loop is the PR event loop:
each rework is a commit (`factory: rework round <n>`), visible in the PR history.

## Every station is a command

The workflows only do the GitHub side (read the issue, push, open the PR, post comments).
Each station is a `factory ci` command that works on the checkout, so you can reproduce
any CI step on your laptop:

```bash
factory ci intake --issue-file issue.md                      # -> warehouse/specs/<id>.yaml, factory-out/comment.md
factory ci implement --spec warehouse/specs/<id>.yaml [--feedback factory-out/feedback.md]
factory ci bi --spec warehouse/specs/<id>.yaml
factory ci checks --spec warehouse/specs/<id>.yaml           # deterministic gates, exit 1 on failure
factory ci review --spec warehouse/specs/<id>.yaml --base origin/main --pr-body pr.md
factory ci governance --product <id>
factory ci feedback                                          # merge findings -> factory-out/feedback.md
factory ci line-manager --runs <dir with downloaded traces>
factory ci collect-runs traces/                              # summaries + traces for artifact upload
```

Each command builds an isolated workspace from the checkout, runs the agent there and copies
only its deliverable back. It writes markdown and JSON to `factory-out/` and step outputs
(`status`, `product_id`, `verdict`, `compliant`, `has_findings`, ...) to `$GITHUB_OUTPUT`.
`tests/test_ci.py` runs the whole pipeline with scripted agents, including a planted bug
that is caught and reworked.

## Setting it up on a repository

1. **Secrets**
   - `ANTHROPIC_API_KEY`: the agents' credentials.
   - `FACTORY_TOKEN`: a GitHub App installation token or fine-grained PAT with contents,
     pull requests and issues write. Pushes and PRs made with the default `GITHUB_TOKEN` do
     not trigger other workflows, so without it the PR half never starts on its own.
2. **Settings → Actions → General**: enable *Allow GitHub Actions to create and approve pull
   requests* (or use an App token) so the review agent can approve. Without it, the review is
   posted as a comment.
3. **Variables** (optional)
   - `FACTORY_AUTO_MERGE=true`: let the factory merge green PRs. Without it the PR is labelled
     `factory:approved` and waits for a human. Combine it with branch protection that requires
     the `checks` job.
   - `FACTORY_MAX_REWORK` (default 2): rework rounds before handing over to a human.
   - `FACTORY_MODEL`: model for every agent (default `claude-haiku-5-5`).
   - `FACTORY_AGENT_<STATION>`: plug another agent directory into a station, e.g.
     `FACTORY_AGENT_BI=agents/bi-teamx`.
4. **Issue template**: `.github/ISSUE_TEMPLATE/data-product-request.yml` adds the label that
   starts the line.

Every agent run is capped by `max_budget_usd` in its `agent.yaml`; jobs have timeouts.
PRs from forks get no secrets, so the agent jobs only run on branches of the repository.

## In the capstone

- The final challenge and its practice runs use `competition.yml`, not the issue → PR pipeline:
  [competition.md](competition.md). Teams run it in their fork with their own
  `ANTHROPIC_API_KEY` secret; the final runs in the organisers' repository.
- In a fork with the secrets above, the issue → PR pipeline works too: label an issue
  `data-product-request` and watch the line open, review and rework a PR.
- A PR inside one repository that changes `agents/<station>/` can carry the `run-benchmark` label.
  The benchmark result is posted on the PR: an evaluation gate for prompt changes. PRs from forks
  get no secrets, so this does not run on the pull request a team opens to the organisers.
- The line manager track gets real traces: everything the pipelines do is uploaded as
  `factory-traces-*` artifacts in the same format as `runs/`.
