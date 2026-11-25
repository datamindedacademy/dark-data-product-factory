"""Run one agent of the factory line in a workspace. Every agent is an Agno agent (https://docs.agno.com).

An agent is a directory under ``agents/`` (see ``agents/README.md``)::

    agents/intake/
      agent.yaml         model, effort, tools, skills, turn limit ...
      system_prompt.md   who the agent is and how it works
      prompt.md          the task message; $placeholders are filled per run
      skills/<name>/SKILL.md   optional skills, loaded when listed in agent.yaml
      tools.py           optional: extra tools (def build_tools(ws) -> list of functions)
      agent.py           optional: build the agent yourself (def build_agent(ws, cfg) -> agno.agent.Agent).
                         Without it the runner builds one from agent.yaml (default_agent below).
      CLAUDE.md          optional: repo context, appended to the instructions

Everything that shapes the agent's context lives in that directory, so the
benchmark can compare two variants by pointing ``--agent-dir`` at a copy.
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import importlib.util
import inspect
import json
import os
import re
import string
from contextlib import nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from factory import llm, paths, phoenix, workspace
from factory.tracing import Tracer

DEFAULT_MODEL = llm.DEFAULT_MODEL


@dataclass
class AgentConfig:
    name: str
    dir: Path
    model: str = DEFAULT_MODEL
    effort: str | None = None
    max_turns: int = 60                  # Agno tool_call_limit
    system_prompt: str = "system_prompt.md"
    prompt: str = "prompt.md"
    # Read: read and list files, Write: save files, Edit: replace lines, Glob: find files, Grep: search contents,
    # Bash: a shell in the workspace
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
        """Hash of every file in the agent dir except its README - identifies the variant in results."""
        h = hashlib.sha256()
        for f in sorted(self.dir.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and f.name != "README.md":
                h.update(str(f.relative_to(self.dir)).encode())
                h.update(f.read_bytes())
        return h.hexdigest()[:10]


def _render(text: str, ctx: dict[str, Any]) -> str:
    return string.Template(text).safe_substitute({k: str(v) for k, v in ctx.items()})


def _load(path: Path) -> Any:
    """Import a Python file from an agent directory (tools.py, agent.py)."""
    spec = importlib.util.spec_from_file_location(f"agent_{path.parent.name}_{path.stem}".replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def _env() -> dict[str, str]:
    return {**os.environ, "DO_NOT_TRACK": "1", "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
            "PATH": f"{paths.BIN}{os.pathsep}{os.environ.get('PATH', '')}"}


def bash_tool(ws: Path):
    async def bash(command: str, timeout: int = 600) -> str:
        """Run a bash command in the workspace (dbt, dct, checkup and factory are on the PATH).
        Returns the exit code and the last 8000 characters of stdout and stderr."""
        proc = await asyncio.create_subprocess_shell(command, cwd=ws, env=_env(), executable="/bin/bash",
                                                     stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout)
        except TimeoutError:
            proc.kill()
            return f"error: timed out after {timeout} s"
        return f"exit {proc.returncode}\n{out.decode(errors='replace')[-8000:]}"
    return bash


def _in_thread(fn: Any) -> Any:
    """An async version of a blocking tool, so parallel agents (review and governance) keep running."""
    if not callable(fn) or inspect.iscoroutinefunction(fn) or not inspect.isfunction(fn):
        return fn

    @functools.wraps(fn)
    async def run(*args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(fn, *args, **kwargs)
    return run


def _tools(cfg: AgentConfig, ws: Path) -> list[Any]:
    """agent.yaml's builtin_tools, mcp and tools.py as Agno tools."""
    from agno.tools.file import FileTools
    from agno.tools.mcp import MCPTools

    from factory.tools import checkup, warehouse

    b = set(cfg.builtin_tools)
    tools: list[Any] = []
    if b & {"Read", "Write", "Edit", "Glob", "Grep"}:  # FileTools keeps every path inside base_dir
        tools.append(FileTools(base_dir=ws, enable_read_file="Read" in b, enable_read_file_chunk="Read" in b,
                               enable_list_files=bool(b & {"Read", "Glob"}), enable_search_files="Glob" in b,
                               enable_search_content="Grep" in b, enable_save_file="Write" in b,
                               enable_replace_file_chunk="Edit" in b))
    if "Bash" in b:
        tools.append(bash_tool(ws))
    for name, sel in (cfg.mcp or {}).items():
        if not sel:
            continue
        if name == "warehouse":
            tools += warehouse.build_tools(ws / "warehouse" / "warehouse.duckdb", sel if isinstance(sel, list) else None)
        elif name == "governance":
            tools.append(checkup.build_tool(ws / "warehouse"))
        elif name == "dct":
            # dbt charts ships its own MCP server: schema browsing, validation, rendering.
            tools.append(MCPTools(command=f"{paths.tool('dct')} mcp serve --project-dir {ws / 'warehouse'}",
                                  env={**_env(), "DO_NOT_TRACK": "1"}, timeout_seconds=60))
        else:
            raise ValueError(f"unknown MCP server {name!r} in {cfg.dir}/agent.yaml")
    if (cfg.dir / "tools.py").exists():
        tools += _load(cfg.dir / "tools.py").build_tools(ws)
    return [_in_thread(t) for t in tools]


def default_agent(ws: Path, cfg: AgentConfig):
    """The agent agent.yaml describes, when the directory has no agent.py."""
    from agno.agent import Agent
    from agno.skills import LocalSkills, Skills

    instructions = _render((cfg.dir / cfg.system_prompt).read_text(), {"workspace": ws})
    if (cfg.dir / "CLAUDE.md").exists():
        instructions += "\n\n" + (cfg.dir / "CLAUDE.md").read_text()
    return Agent(
        model=llm.model(cfg.model, cfg.effort),
        instructions=instructions,
        tools=_tools(cfg, ws),
        skills=Skills(loaders=[LocalSkills(str(cfg.dir / "skills" / n)) for n in cfg.skills]) if cfg.skills else None,
        tool_call_limit=cfg.max_turns,
        telemetry=False,
    )


_PATH_KEYS = ("file_path", "path", "notebook_path", "file_name", "directory")


def _escapes(ws: Path, tool: str, args: dict[str, Any]) -> str | None:
    """Why this tool call reaches outside the workspace, or None. The repository holds the golden answers."""
    for k in _PATH_KEYS:
        if isinstance(args.get(k), str) and not (ws / args[k]).resolve().is_relative_to(ws.resolve()):
            return f"{k} {args[k]} is outside the workspace"
    cmd = args.get("command") if tool.lower() in ("bash", "run_shell_command") else None
    if tool == "run_shell_command" and isinstance(args.get("args"), list):
        cmd = " ".join(map(str, args["args"]))
    if cmd is not None:
        # ponytail: string match, not a jail. Stops an agent wandering into the repo (it did: it read the
        # golden specs); a determined `find /` still gets out. Real isolation = a container per run.
        cmd = str(cmd)
        for allowed, alias in ((ws.resolve(), "."), (ws, "."), (paths.ROOT / ".venv", "venv")):  # the tools live in .venv
            cmd = cmd.replace(str(allowed), alias)
        if str(paths.ROOT) in cmd or re.search(r"(^|[\s=:'\"])(~|\$HOME|\$\{HOME\})", cmd) or re.search(r"(^|[\s/'\"=])\.\.(/|\s|$|['\"])", cmd) or re.search(r"(^|\s)(cd|pushd)\s*($|[;&|~])", cmd):
            return "the command leaves the workspace"
    return None


def workspace_guard(ws: Path):
    """An Agno tool hook that refuses calls reaching outside the workspace, for every agent."""
    async def guard(function_name: str, function_call: Any, arguments: dict[str, Any]) -> Any:
        why = _escapes(ws, function_name, arguments or {})
        if why:
            return f"Denied: {why}. Work only inside {ws}."
        result = function_call(**arguments)
        return await result if asyncio.iscoroutine(result) else result
    return guard


async def run_agent(agent_dir: str | Path, ws: Path, run_dir: Path, ctx: dict[str, Any] | None = None,
                    meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the agent in ``ws``; trace to ``run_dir``. Returns the run summary."""
    cfg = AgentConfig.load(agent_dir)
    ctx = {"workspace": ws, **(ctx or {})}
    prompt = _render((cfg.dir / cfg.prompt).read_text(), ctx)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompt.txt").write_text(prompt)
    tracer = Tracer(run_dir, {"agent": cfg.name, "agent_dir": str(cfg.dir), "agent_fingerprint": cfg.fingerprint(),
                              "framework": "agno", "agent_py": (cfg.dir / "agent.py").exists(),
                              "model": cfg.model, "effort": cfg.effort, **(meta or {})})
    error = None
    attrs = nullcontext()
    if phoenix.setup():  # one Phoenix session per benchmark or e2e run
        from openinference.instrumentation import using_attributes
        session = run_dir.name if run_dir.parent == paths.RUNS else run_dir.parent.name
        attrs = using_attributes(session_id=session,
                                 metadata={"agent": cfg.name, **{k: str(v) for k, v in (meta or {}).items()}})
    try:
        with attrs:
            await _run(cfg, ws, prompt, tracer)
    except Exception as exc:  # noqa: BLE001 - recorded in the trace, graded as a failed run
        error = f"{type(exc).__name__}: {exc}"
    phoenix.flush()
    summary = tracer.close(error)
    missing = [o for o in cfg.outputs if not (ws / _render(o, ctx)).exists()]
    if missing:
        summary["missing_outputs"] = missing
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


async def _run(cfg: AgentConfig, ws: Path, prompt: str, tracer: Tracer) -> None:
    os.environ["PATH"] = _env()["PATH"]  # tools started by the agent must find factory, dbt, dct
    custom = cfg.dir / "agent.py"
    agent = await _maybe_await(_load(custom).build_agent(ws, cfg)) if custom.exists() else default_agent(ws, cfg)
    agent.tool_hooks = [*(getattr(agent, "tool_hooks", None) or []), workspace_guard(ws)]
    tracer.on_agno_run(await agent.arun(prompt), cfg.model)


async def _maybe_await(x: Any) -> Any:
    return await x if asyncio.iscoroutine(x) else x


def run_agent_sync(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_agent(*args, **kwargs))
