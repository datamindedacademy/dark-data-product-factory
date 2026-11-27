"""The base agent every station starts from: an Agno agent that can read and write files, run Python
and shell commands, and query the CSV files with SQL, all inside its workspace.

    from factory.agent import base_agent

    def build(workspace):
        return base_agent(workspace, instructions="You are ...")

Add context with the keyword arguments: more `instructions`, `skills` (folders with a SKILL.md),
`tools` (Python functions or Agno toolkits, an MCP server via `agno.tools.mcp.MCPTools`), or
`effort` to make the model reason before it answers. The model is the same for everyone (`llm.MODEL`).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from factory import llm


def base_agent(workspace: Path, instructions: str, *, effort: str | None = None,
               tools: list[Any] | None = None, skills: list[str | Path] | None = None, max_tool_calls: int = 40):
    """An Agno agent for one workspace.

    effort          None (no reasoning), "low", "medium" or "high"
    tools           extra tools on top of files, shell and SQL
    skills          skill folders, each with a SKILL.md; the agent loads one when it needs it
    max_tool_calls  the run stops after this many tool calls
    """
    from agno.agent import Agent
    from agno.skills import LocalSkills, Skills
    from agno.tools.file import FileTools

    return Agent(
        model=llm.model(effort),
        instructions=instructions,
        tools=[FileTools(base_dir=workspace), shell_tool(workspace), sql_tool(workspace), *(tools or [])],
        skills=Skills(loaders=[LocalSkills(str(s)) for s in skills]) if skills else None,
        tool_call_limit=max_tool_calls,
        telemetry=False,
    )


def shell_tool(ws: Path):
    async def shell(command: str, timeout: int = 300) -> str:
        """Run a shell command in the workspace, e.g. `python output/analysis.py`. Python has duckdb.
        Returns the exit code and the last 8000 characters of the output."""
        proc = await asyncio.create_subprocess_shell(command, cwd=ws, executable="/bin/bash", env=_env(),
                                                     stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout)
        except TimeoutError:
            proc.kill()
            return f"error: timed out after {timeout} s"
        return f"exit {proc.returncode}\n{out.decode(errors='replace')[-8000:]}"
    return shell


def _load(ws: Path):
    """The CSV files as in-memory tables, then no more file access: a query can't read outside data/."""
    import duckdb

    con = duckdb.connect()
    for f in sorted((ws / "data").glob("*.csv")):
        con.execute(f"create table \"{f.stem}\" as select * from read_csv_auto('{f}')")
    con.execute("set enable_external_access = false")
    con.execute("set lock_configuration = true")
    return con


def sql_tool(ws: Path):
    con: list = []  # loaded on the first query, then reused

    def run_sql(query: str, max_rows: int = 50) -> str:
        """Run a DuckDB SQL query on the CSV files in data/. Every file is a table: data/orders.csv is `orders`."""
        if not con:
            con.append(_load(ws))
        try:
            cur = con[0].cursor().execute(query)
            cols = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(max_rows + 1)
        except Exception as exc:  # noqa: BLE001 - the error is the answer the agent needs
            return f"error: {exc}"
        lines = [" | ".join(cols)] + [" | ".join(map(str, r)) for r in rows[:max_rows]]
        return "\n".join(lines) + (f"\n… more than {max_rows} rows" if len(rows) > max_rows else "")
    return run_sql


def _env() -> dict[str, str]:
    venv_bin = Path(__file__).resolve().parents[1] / ".venv" / "bin"
    return {**os.environ, "PATH": f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}"}
