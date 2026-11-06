Review the change on branch `feature` (compare with `main`). The spec it implements is
`input/spec.yaml`; the PR description is `input/pr.md`.

Write your review to `output/review.json`:

```json
{
  "verdict": "approve" | "request_changes",
  "summary": "...",
  "docs_up_to_date": true | false,
  "findings": [
    {"severity": "blocker|major|minor|nit",
     "category": "correctness|spec_mismatch|tests|docs|performance|style|governance",
     "file": "warehouse/models/...", "line": 12, "message": "...", "suggestion": "..."}
  ]
}
```

Validate it with `factory validate review output/review.json`.
