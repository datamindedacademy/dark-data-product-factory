"""In-process MCP tools that give agents read access to the workspace warehouse.

The baseline agents only get ``run_sql``. Giving an agent better data tools
(schema browsing, column profiling, the dbt manifest, a semantic layer...) is
one of the main levers you have in the capstone.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
from claude_agent_sdk import create_sdk_mcp_server, tool

MAX_CELL = 200


def _text(s: str, is_error: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {"content": [{"type": "text", "text": s}]}
    if is_error:
        out["is_error"] = True
    return out


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


def build_server(db: Path, enabled: list[str] | None = None):
    """Build the ``warehouse`` MCP server bound to one DuckDB file."""

    @tool("run_sql",
          "Run a read-only DuckDB SQL query against the warehouse and return up to `limit` rows "
          "(default 50) as a markdown table. Schemas: `raw` (landed source tables) and `main` "
          "(dbt staging + mart models).",
          {"sql": str, "limit": int})
    async def run_sql(args: dict[str, Any]) -> dict[str, Any]:
        try:
            cols, rows, n = query(db, args["sql"], int(args.get("limit") or 50))
        except Exception as exc:  # noqa: BLE001
            return _text(f"SQL error: {exc}", is_error=True)
        if not cols:
            return _text("OK (no result set)")
        return _text(_fmt(cols, rows, n))

    @tool("list_tables", "List every table and view in the warehouse with its schema and row count.", {})
    async def list_tables(args: dict[str, Any]) -> dict[str, Any]:
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
        return _text(_fmt(["schema", "table", "type", "rows"], out))

    @tool("describe_table",
          "Columns, types, null fraction, distinct count and example values of one table "
          "(`schema.table`, e.g. `raw.orders` or `main.fct_orders`).",
          {"table": str})
    async def describe_table(args: dict[str, Any]) -> dict[str, Any]:
        table = args["table"]
        try:
            cols, rows, _ = query(db, f"select column_name, data_type from information_schema.columns "
                                      f"where table_schema || '.' || table_name = '{table}' order by ordinal_position", 500)
            if not rows:
                return _text(f"table {table!r} not found", is_error=True)
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
            return _text(f"{table}: {total} rows\n" + _fmt(["column", "type", "null %", "distinct", "examples"], out))
        except Exception as exc:  # noqa: BLE001
            return _text(f"error: {exc}", is_error=True)

    tools = {"run_sql": run_sql, "list_tables": list_tables, "describe_table": describe_table}
    selected = [tools[n] for n in (enabled or tools)]
    return create_sdk_mcp_server("warehouse", tools=selected)
