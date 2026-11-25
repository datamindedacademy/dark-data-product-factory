"""Tools that give agents read access to the workspace warehouse (plain functions for Agno).

The baseline agents only get ``run_sql``. Giving an agent better data tools
(schema browsing, column profiling, the dbt manifest, a semantic layer...) is
one of the main levers you have in the capstone.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

MAX_CELL = 200


def _fmt(cols: list[str], rows: list[tuple], total: int | None = None) -> str:
    def cell(v: Any) -> str:
        s = "NULL" if v is None else str(v)
        return s if len(s) <= MAX_CELL else s[:MAX_CELL] + "…"

    lines = [" | ".join(cols), " | ".join("---" for _ in cols)]
    lines += [" | ".join(cell(v) for v in r) for r in rows]
    if total is not None and total > len(rows):
        lines.append(f"... {total - len(rows)} more rows not shown")
    return "\n".join(lines)


def query(db: Path, sql: str, limit: int = 50) -> tuple[list[str], list[tuple], int]:
    con = duckdb.connect(str(db), read_only=True)
    try:
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(limit + 1)
        return cols, rows[:limit], len(rows)
    finally:
        con.close()


def run_sql_text(db: Path, sql: str, limit: int = 50) -> str:
    """``run_sql`` as a plain function, for agents that are not built on the Agent SDK (see agents/intake-agno)."""
    try:
        cols, rows, n = query(db, sql, limit)
    except Exception as exc:  # noqa: BLE001
        return f"SQL error: {exc}"
    return _fmt(cols, rows, n) if cols else "OK (no result set)"


def build_tools(db: Path, enabled: list[str] | None = None) -> list:
    """The warehouse tools bound to one DuckDB file, as functions an Agno agent can call."""

    def run_sql(sql: str, limit: int = 50) -> str:
        """Run a read-only DuckDB SQL query against the warehouse and return up to `limit` rows (default 50)
        as a markdown table. Schemas: `raw` (landed source tables) and `main` (dbt staging + mart models)."""
        return run_sql_text(db, sql, int(limit or 50))

    def list_tables() -> str:
        """List every table and view in the warehouse with its schema and row count."""
        cols, rows, _ = query(db, """
            select table_schema, table_name, table_type
            from information_schema.tables
            where table_schema in ('raw', 'main')
            order by 1, 2""", 500)
        out = []
        con = duckdb.connect(str(db), read_only=True)
        try:
            for schema, name, kind in rows:
                n = con.execute(f'select count(*) from "{schema}"."{name}"').fetchone()[0]
                out.append((schema, name, kind, n))
        finally:
            con.close()
        return _fmt(["schema", "table", "type", "rows"], out)

    def describe_table(table: str) -> str:
        """Columns, types, null fraction, distinct count and example values of one table
        (`schema.table`, e.g. `raw.orders` or `main.fct_orders`)."""
        try:
            cols, rows, _ = query(db, f"select column_name, data_type from information_schema.columns "
                                      f"where table_schema || '.' || table_name = '{table}' order by ordinal_position", 500)
            if not rows:
                return f"error: table {table!r} not found"
            con = duckdb.connect(str(db), read_only=True)
            out = []
            try:
                total = con.execute(f"select count(*) from {table}").fetchone()[0]
                for name, dtype in rows:
                    nulls, distinct = con.execute(
                        f'select count(*) - count("{name}"), count(distinct "{name}") from {table}').fetchone()
                    ex = [r[0] for r in con.execute(
                        f'select distinct "{name}" from {table} where "{name}" is not null limit 5').fetchall()]
                    out.append((name, dtype, f"{nulls / total:.1%}" if total else "-", distinct, json.dumps(ex, default=str)[:160]))
            finally:
                con.close()
            return f"{table}: {total} rows\n" + _fmt(["column", "type", "null %", "distinct", "examples"], out)
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    tools = {"run_sql": run_sql, "list_tables": list_tables, "describe_table": describe_table}
    return [tools[n] for n in (enabled or tools)]
