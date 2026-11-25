"""The intake agent written out as an Agno agent (https://docs.agno.com).

The factory runner calls ``build_agent(ws, cfg)`` and then ``agent.arun(<rendered prompt.md>)``.
``ws`` is the run's workspace (a copy of the company repo), ``cfg`` is this directory's agent.yaml.
Everything else is yours: tools, skills, MCP servers, model, a team of agents.

    factory run intake --agent-dir agents/intake-agno --case intake-01-category
"""

from pathlib import Path

from agno.agent import Agent
from agno.tools.file import FileTools

from factory import llm
from factory.runner import bash_tool
from factory.tools.warehouse import run_sql_text


def build_agent(ws: Path, cfg) -> Agent:
    def run_sql(sql: str, limit: int = 50) -> str:
        """Run a read-only DuckDB query on the warehouse (schemas `raw` and `main`); returns a markdown table."""
        return run_sql_text(ws / "warehouse" / "warehouse.duckdb", sql, limit)

    return Agent(
        model=llm.model(cfg.model),
        instructions=(cfg.dir / cfg.system_prompt).read_text(),
        tools=[run_sql, FileTools(base_dir=ws), bash_tool(ws)],
        tool_call_limit=cfg.max_turns,
        telemetry=False,
        # Block 2 - skills:  skills=Skills(loaders=[LocalSkills(str(cfg.dir / "skills"))])   (from agno.skills)
        # Block 3 - MCP:     add MCPTools(command=f"dct mcp serve --project-dir {ws / 'warehouse'}")  (from agno.tools.mcp)
        #                    to tools, or point MCPTools at a server you wrote yourself (mcp/<name>.py).
    )
