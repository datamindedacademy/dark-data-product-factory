"""Run a spec's executable acceptance checks against a DuckDB warehouse.

The intake agent writes acceptance checks; the implementation agent (and the
benchmark) run them to decide whether the implementation answers the business
questions. SQL may use ``{{ ref('model') }}`` and ``{{ source('raw', 'table') }}``.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import duckdb

from factory.contracts import AcceptanceCheck, DataProductSpec, Expectation

_REF = re.compile(r"\{\{\s*ref\(\s*['\"]([\w]+)['\"]\s*\)\s*\}\}")
_SRC = re.compile(r"\{\{\s*source\(\s*['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\s*\)\s*\}\}")


def render_sql(sql: str) -> str:
    sql = _REF.sub(lambda m: f"main.{m.group(1)}", sql)
    return _SRC.sub(lambda m: f"{m.group(1)}.{m.group(2)}", sql)


@dataclass
class CheckResult:
    id: str
    passed: bool
    detail: str
    actual: Any = None
    expected: Any = None


@dataclass
class AcceptanceReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(r.passed for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def score(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def as_text(self) -> str:
        lines = [f"{self.passed}/{self.total} acceptance checks passed"]
        for r in self.results:
            mark = "PASS" if r.passed else "FAIL"
            lines.append(f"  [{mark}] {r.id}: {r.detail}")
        return "\n".join(lines)


def _close(a: Any, b: Any, tol: float) -> bool:
    if a is None or b is None:
        return a is b
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return str(a).strip().lower() == str(b).strip().lower()
    if math.isclose(fa, fb, rel_tol=tol, abs_tol=1e-9):
        return True
    return abs(fa - fb) <= tol * max(abs(fa), abs(fb), 1.0)


def _rows_match(actual: list[tuple], expected: list[tuple], tol: float, ordered: bool) -> bool:
    if len(actual) != len(expected):
        return False
    if not ordered:
        actual = sorted(actual, key=lambda r: tuple(str(x) for x in r))
        expected = sorted(expected, key=lambda r: tuple(str(x) for x in r))
    for ra, re_ in zip(actual, expected):
        if len(ra) != len(re_):
            return False
        if not all(_close(x, y, tol) for x, y in zip(ra, re_)):
            return False
    return True


def evaluate(con: duckdb.DuckDBPyConnection, check: AcceptanceCheck) -> CheckResult:
    e: Expectation = check.expect
    try:
        rows = con.execute(render_sql(check.sql)).fetchall()
    except Exception as exc:  # noqa: BLE001 - any SQL error is a failed check
        return CheckResult(check.id, False, f"query failed: {str(exc).splitlines()[0][:200]}")
    first = rows[0][0] if rows and rows[0] else None
    if e.type == "non_empty":
        return CheckResult(check.id, bool(rows), f"{len(rows)} rows", len(rows), ">0")
    if e.type == "empty":
        return CheckResult(check.id, not rows, f"{len(rows)} rows", len(rows), 0)
    if e.type == "row_count":
        return CheckResult(check.id, len(rows) == int(e.value), f"{len(rows)} rows, expected {e.value}", len(rows), e.value)
    if e.type == "equals":
        ok = _close(first, e.value, e.tolerance)
        return CheckResult(check.id, ok, f"got {first!r}, expected {e.value!r}", first, e.value)
    if e.type == "between":
        try:
            ok = first is not None and e.min <= float(first) <= e.max
        except (TypeError, ValueError):
            ok = False
        return CheckResult(check.id, ok, f"got {first!r}, expected in [{e.min}, {e.max}]", first, [e.min, e.max])
    if e.type == "matches_reference":
        try:
            ref_rows = con.execute(render_sql(e.reference_sql or "")).fetchall()
        except Exception as exc:  # noqa: BLE001
            return CheckResult(check.id, False, f"reference query failed: {str(exc).splitlines()[0][:200]}")
        ok = _rows_match(rows, ref_rows, e.tolerance, e.ordered)
        show = lambda rs: rs[:3] if len(rs) > 3 else rs  # noqa: E731
        return CheckResult(check.id, ok, f"got {show(rows)}, reference {show(ref_rows)}", rows, ref_rows)
    raise ValueError(e.type)


def run_acceptance(spec: DataProductSpec, db_path: str | Path) -> AcceptanceReport:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        report = AcceptanceReport()
        for q in spec.business_questions:
            for check in q.acceptance:
                report.results.append(evaluate(con, check))
        return report
    finally:
        con.close()


def main() -> None:  # python -m factory.acceptance spec.yaml warehouse.duckdb
    import sys

    spec = DataProductSpec.load(sys.argv[1])
    report = run_acceptance(spec, sys.argv[2])
    print(report.as_text())
    raise SystemExit(0 if report.passed == report.total else 1)


if __name__ == "__main__":
    main()
