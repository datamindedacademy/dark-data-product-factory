# Track: Governance agent

**Station.** Checks a data product against `standards/data-product-standards.md` and
reports violations by rule id (`output/governance.json`). A deterministic linter
(`checkup`, also `factory checkup`) covers GOV-001..005, 007, 009. The rest need
judgement: PII (GOV-006), naming of measures and ratios (GOV-008), dashboard (GOV-010),
business rules (GOV-011).

```bash
factory run governance --case governance-03-judgement
factory bench run governance --repeat 3
```

**Seed cases.** A compliant product (no false violations!), one with mechanical
violations, one that passes the linter but breaks the judgement rules.

**Ideas to improve**
- Treat `checkup` as the first step, not the answer; give a method per judgement rule.
- Tools for the judgement rules: column profiling to detect PII by content, a check that
  the board exists and validates, SQL to test whether QA accounts are in the output.
- Extend `factory/tools/checkup.py` with rules that *can* be made mechanical (e.g. the
  `accepted_range` part of GOV-008). Measure what the LLM still adds.
- Precision matters: one violation per rule per model, exact model names.
- Stretch: suggest the fix as a patch, or wire it as a CI gate.

**Benchmark ideas.** PII hidden in a free-text column; a monetary column without `_eur`;
a board that reads raw tables; a product that is compliant but looks suspicious.
