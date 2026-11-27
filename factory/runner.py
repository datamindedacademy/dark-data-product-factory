"""Run one agent in a workspace. An agent is a folder under agents/ with an agent.py:

    TASK = "Read input/issue.md and write output/spec.json ..."   # the message the agent gets

    def build(workspace):                                         # returns an Agno agent
        return base_agent(workspace, instructions=...)

Everything that shapes the agent lives in that folder, so the benchmark can compare two
versions of an agent by pointing --agent at a copy.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import re
import string
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from factory import llm, paths, phoenix
from factory.tracing import Tracer


def load(agent_dir: Path) -> Any:
    """Import agents/<name>/agent.py."""
    path = agent_dir / "agent.py"
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    spec = importlib.util.spec_from_file_location(f"agent_{agent_dir.name}".replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def fingerprint(agent_dir: Path) -> str:
    """A hash of every file in the agent folder except its README: tells versions apart in results."""
    h = hashlib.sha256()
    for f in sorted(agent_dir.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts and f.name != "README.md":
            h.update(str(f.relative_to(agent_dir)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()[:10]


def _escapes(ws: Path, tool: str, args: dict[str, Any]) -> str | None:
    """Why this tool call reaches outside the workspace, or None. The repository holds the right answers."""
    for k in ("file_path", "path", "file_name", "directory"):
        if isinstance(args.get(k), str) and not (ws / args[k]).resolve().is_relative_to(ws.resolve()):
            return f"{k} {args[k]} is outside the workspace"
    if tool == "shell" and isinstance(args.get("command"), str):
        # ponytail: string match, not a jail. Stops an agent wandering into the repo; a determined
        # `find /` still gets out. Real isolation = a container per run.
        cmd = args["command"]
        for allowed in (str(ws.resolve()), str(ws)):
            cmd = cmd.replace(allowed, ".")
        cmd = cmd.replace(str(paths.ROOT / ".venv"), "venv")
        if str(paths.ROOT) in cmd or re.search(r"(^|[\s=:'\"])(~|\$HOME|\$\{HOME\})", cmd) \
                or re.search(r"(^|[\s/'\"=])\.\.(/|\s|$|['\"])", cmd) or re.search(r"(^|\s)(cd|pushd)\s*($|[;&|~])", cmd):
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


async def run_agent(agent_dir: Path, ws: Path, run_dir: Path, ctx: dict[str, Any] | None = None,
                    meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the agent in `ws`, trace to `run_dir`. Returns the run summary."""
    agent_dir = Path(agent_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    meta = {"agent": agent_dir.name, "agent_dir": str(agent_dir), "agent_fingerprint": fingerprint(agent_dir),
            **(meta or {})}
    error = None
    tracer = None
    try:
        mod = load(agent_dir)
        task = string.Template(mod.TASK).safe_substitute({k: str(v) for k, v in (ctx or {}).items()})
        (run_dir / "task.txt").write_text(task)
        agent = mod.build(ws)
        agent = await agent if asyncio.iscoroutine(agent) else agent
        agent.tool_hooks = [*(agent.tool_hooks or []), workspace_guard(ws)]
        model = getattr(agent.model, "id", "?")
        if model != llm.MODEL:
            raise ValueError(f"{agent_dir.name} uses {model}: every agent runs on {llm.MODEL}")
        tracer = Tracer(run_dir, {**meta, "model": model})
        attrs = nullcontext()
        if phoenix.setup():  # one Phoenix session per benchmark or line run
            from openinference.instrumentation import using_attributes
            session = run_dir.name if run_dir.parent == paths.RUNS else run_dir.parent.name
            attrs = using_attributes(session_id=session, metadata={k: str(v) for k, v in meta.items()})
        with attrs:
            tracer.on_agno_run(await agent.arun(task), model)
    except Exception as exc:  # noqa: BLE001 - recorded in the trace, graded as a failed run
        error = f"{type(exc).__name__}: {exc}"
    phoenix.flush()
    if tracer is None:
        tracer = Tracer(run_dir, meta)
    return tracer.close(error)


def run_agent_sync(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_agent(*args, **kwargs))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, default=str))
