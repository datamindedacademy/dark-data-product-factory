"""Run one agent of the factory line in a workspace with the Claude Agent SDK.

An agent is a directory under ``agents/`` (see ``agents/README.md``)::

    agents/intake/
      agent.yaml         model, effort, tools, skills, budgets ...
      system_prompt.md   who the agent is and how it works
      prompt.md          the task message; $placeholders are filled per run
      skills/<name>/SKILL.md   optional skills (installed into the workspace)
      tools.py           optional: extra in-process MCP tools (def build_tools(ws) -> list)
      CLAUDE.md          optional: repo context file placed at the workspace root

Everything that shapes the agent's context lives in that directory, so the
benchmark can compare two variants by pointing ``--agent-dir`` at a copy.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query

from factory import paths, workspace
from factory.tracing import Tracer

DEFAULT_MODEL = os.environ.get("FACTORY_MODEL") or "claude-opus-5-5"


@dataclass
class AgentConfig:
    name: str
    dir: Path
    model: str = DEFAULT_MODEL
    effort: str | None = None
    max_turns: int = 60
    max_budget_usd: float | None = None
    system_prompt: str = "system_prompt.md"
    system_prompt_mode: str = "replace"  # replace | append (to the Claude Code system prompt)
    prompt: str = "prompt.md"
    builtin_tools: list[str] = field(default_factory=lambda: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"])
    mcp: dict[str, Any] = field(default_factory=dict)  # {"warehouse": ["run_sql"], "governance": ["checkup"], "dct": true}
    skills: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)  # files the agent must write (relative to workspace)

    @classmethod
    def load(cls, agent_dir: str | Path) -> "AgentConfig":
        agent_dir = Path(agent_dir).resolve()
        raw = yaml.safe_load((agent_dir / "agent.yaml").read_text()) or {}
        raw.pop("description", None)
        if raw.get("model") in (None, "default"):
            raw["model"] = DEFAULT_MODEL
        raw.setdefault("name", agent_dir.name)
        return cls(dir=agent_dir, **raw)

    def fingerprint(self) -> str:
        """Hash of every file in the agent dir - identifies the variant in results."""
        h = hashlib.sha256()
        for f in sorted(self.dir.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                h.update(str(f.relative_to(self.dir)).encode())
                h.update(f.read_bytes())
        return h.hexdigest()[:10]


def _render(text: str, ctx: dict[str, Any]) -> str:
    return string.Template(text).safe_substitute({k: str(v) for k, v in ctx.items()})


def _mcp_servers(cfg: AgentConfig, ws: Path) -> tuple[dict[str, Any], list[str]]:
    from factory.tools import checkup, warehouse

    servers: dict[str, Any] = {}
    allowed: list[str] = []
    db = ws / "warehouse" / "warehouse.duckdb"
    for name, sel in (cfg.mcp or {}).items():
        if not sel:
            continue
        if name == "warehouse":
            tools = sel if isinstance(sel, list) else None
            servers["warehouse"] = warehouse.build_server(db, tools)
            allowed += [f"mcp__warehouse__{t}" for t in (tools or ["run_sql", "list_tables", "describe_table"])]
        elif name == "governance":
            servers["governance"] = checkup.build_server(ws / "warehouse")
            allowed.append("mcp__governance__checkup")
        elif name == "dct":
            # dbt charts ships its own MCP server (`dct mcp serve`): schema browsing, validation, rendering.
            servers["dct"] = {"type": "stdio", "command": paths.tool("dct"), "args": ["mcp", "serve", "--project-dir", str(ws / "warehouse")],
                              "env": {"DO_NOT_TRACK": "1"}}
            allowed.append("mcp__dct")
        else:
            raise ValueError(f"unknown MCP server {name!r} in {cfg.dir}/agent.yaml")

    custom = cfg.dir / "tools.py"
    if custom.exists():
        spec = importlib.util.spec_from_file_location(f"agent_tools_{cfg.name}", custom)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(mod)
        tools = mod.build_tools(ws)
        if tools:
            servers["custom"] = create_sdk_mcp_server("custom", tools=tools)
            allowed += [f"mcp__custom__{t.name}" for t in tools]
    return servers, allowed


def build_options(cfg: AgentConfig, ws: Path) -> ClaudeAgentOptions:
    system = _render((cfg.dir / cfg.system_prompt).read_text(), {"workspace": ws})
    system_prompt: Any = system
    if cfg.system_prompt_mode == "append":
        system_prompt = {"type": "preset", "preset": "claude_code", "append": system}
    servers, mcp_allowed = _mcp_servers(cfg, ws)
    return ClaudeAgentOptions(
        model=cfg.model,
        effort=cfg.effort,
        system_prompt=system_prompt,
        cwd=str(ws),
        tools=list(cfg.builtin_tools),
        allowed_tools=list(cfg.builtin_tools) + mcp_allowed,
        disallowed_tools=["WebFetch", "WebSearch"],
        mcp_servers=servers,
        skills=list(cfg.skills) if cfg.skills else [],
        # Only load settings/CLAUDE.md from the workspace, never from the user's machine:
        # benchmark runs must not depend on whoever runs them.
        setting_sources=["project"],
        permission_mode="acceptEdits",
        max_turns=cfg.max_turns,
        max_budget_usd=cfg.max_budget_usd,
        env={"DO_NOT_TRACK": "1", "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
             "PATH": f"{paths.BIN}{os.pathsep}{os.environ.get('PATH', '')}"},
    )


async def run_agent(agent_dir: str | Path, ws: Path, run_dir: Path, ctx: dict[str, Any] | None = None,
                    meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the agent in ``ws``; trace to ``run_dir``. Returns the run summary."""
    cfg = AgentConfig.load(agent_dir)
    workspace.install_agent_context(ws, cfg.dir, cfg.skills)
    ctx = {"workspace": ws, **(ctx or {})}
    prompt = _render((cfg.dir / cfg.prompt).read_text(), ctx)
    (run_dir / "prompt.txt").write_text(prompt)
    tracer = Tracer(run_dir, {"agent": cfg.name, "agent_dir": str(cfg.dir), "agent_fingerprint": cfg.fingerprint(),
                              "model": cfg.model, "effort": cfg.effort, **(meta or {})})
    error = None
    try:
        async for msg in query(prompt=prompt, options=build_options(cfg, ws)):
            tracer.on_message(msg)
    except Exception as exc:  # noqa: BLE001 - recorded in the trace, graded as a failed run
        error = f"{type(exc).__name__}: {exc}"
    summary = tracer.close(error)
    missing = [o for o in cfg.outputs if not (ws / _render(o, ctx)).exists()]
    if missing:
        summary["missing_outputs"] = missing
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def run_agent_sync(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_agent(*args, **kwargs))
