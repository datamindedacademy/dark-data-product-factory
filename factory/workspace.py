"""Isolated workspaces: every agent run gets its own copy of the company repo.

A workspace mirrors the layout an agent would see in a real checkout::

    <ws>/
      warehouse/            dbt + dbt charts project, with its own warehouse.duckdb
      standards/            organisational standards (governance rules)
      input/                files handed to the agent (issue.md, spec.yaml, ...)
      output/               files the agent must produce (spec.yaml, review.json, ...)
      .claude/skills/       skills installed for this agent
      CLAUDE.md             optional repo-level context (copied from the agent dir)

The workspace is a git repository whose ``main`` branch holds the base project.
Stages that review a change (review, governance) get the change as a commit on
branch ``feature`` so the agent can ``git diff main...feature``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from factory import paths

_IGNORE = shutil.ignore_patterns("target", "logs", "renders", "dbt_packages", "*.duckdb.wal", ".user.yml")


def env() -> dict[str, str]:
    e = dict(os.environ)
    e.setdefault("DO_NOT_TRACK", "1")  # dbt charts + dbt anonymous telemetry
    e.setdefault("DBT_SEND_ANONYMOUS_USAGE_STATS", "false")
    e["PATH"] = f"{paths.BIN}{os.pathsep}{e.get('PATH', '')}"
    return e


def sh(cmd: list[str] | str, cwd: Path, check: bool = True, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env(), shell=isinstance(cmd, str), check=check,
                          capture_output=True, text=True, timeout=timeout)


def new_run_id(prefix: str) -> str:
    return f"{datetime.now():%Y%m%d-%H%M%S}-{prefix}-{uuid.uuid4().hex[:6]}"


def _git(ws: Path, *args: str) -> None:
    sh(["git", "-c", "user.name=factory", "-c", "user.email=factory@fernhill.test", *args], ws)


def create(run_dir: Path) -> Path:
    """Copy the base project into ``run_dir/workspace`` and commit it on ``main``."""
    if not paths.WAREHOUSE_DB.exists():
        raise SystemExit("warehouse/warehouse.duckdb missing - run `factory setup` first")
    ws = run_dir / "workspace"
    ws.mkdir(parents=True)
    shutil.copytree(paths.WAREHOUSE, ws / "warehouse", ignore=_IGNORE)
    shutil.copytree(paths.STANDARDS, ws / "standards")
    (ws / "input").mkdir()
    (ws / "output").mkdir()
    (ws / ".gitignore").write_text("warehouse/*.duckdb\nwarehouse/*.duckdb.wal\nwarehouse/target/\n"
                                    "warehouse/logs/\nwarehouse/renders/\n.claude/\n")
    _git(ws, "init", "-q", "-b", "main")
    _git(ws, "add", "-A")
    _git(ws, "commit", "-q", "-m", "base project")
    return ws


def install_product(ws: Path, product: str, board: bool = True) -> None:
    """Copy a golden data product (models + board) into the workspace."""
    src = paths.PRODUCTS / product
    dst = ws / "warehouse" / "models" / "marts" / product
    shutil.copytree(src / "models", dst, dirs_exist_ok=True)
    if board and (src / "board.yml").exists():
        shutil.copy(src / "board.yml", ws / "warehouse" / "charts" / f"{product}.yml")


def overlay(ws: Path, overlay_dir: Path) -> None:
    """Copy files from ``overlay_dir`` over the workspace (paths relative to ws root).

    A file named ``<name>.delete`` deletes ``<name>``.
    """
    for f in overlay_dir.rglob("*"):
        if f.is_dir():
            continue
        rel = f.relative_to(overlay_dir)
        target = ws / rel
        if f.name.endswith(".delete"):
            target.with_name(f.name[: -len(".delete")]).unlink(missing_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, target)


def branch(ws: Path, name: str) -> None:
    _git(ws, "checkout", "-q", "-b", name)


def commit(ws: Path, message: str, branch: str | None = None) -> None:
    if branch:
        _git(ws, "checkout", "-q", "-b", branch)
    _git(ws, "add", "-A")
    _git(ws, "commit", "-q", "--allow-empty", "-m", message)


def copy_db(ws: Path) -> None:
    shutil.copy(paths.WAREHOUSE_DB, ws / "warehouse" / "warehouse.duckdb")


def dbt(ws: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return sh([paths.tool("dbt"), *args], ws / "warehouse", check=check)


def dct(ws: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return sh([paths.tool("dct"), "--no-send-anonymous-usage-stats", *args], ws / "warehouse", check=check)


def install_agent_context(ws: Path, agent_dir: Path, skills: list[str]) -> None:
    """Install the agent's skills (and optional CLAUDE.md) into the workspace."""
    for name in skills:
        src = agent_dir / "skills" / name
        if not (src / "SKILL.md").exists():
            raise FileNotFoundError(f"skill {name!r} not found at {src}/SKILL.md")
        shutil.copytree(src, ws / ".claude" / "skills" / name, dirs_exist_ok=True)
    if (agent_dir / "CLAUDE.md").exists():
        shutil.copy(agent_dir / "CLAUDE.md", ws / "CLAUDE.md")
