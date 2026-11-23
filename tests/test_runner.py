"""The workspace guard: agents must not read the repository (it holds the golden answers)."""

import pytest

from factory import paths
from factory.runner import _escapes

WS = paths.RUNS / "x" / "workspace"


@pytest.mark.parametrize("tool,args,escapes", [
    ("Read", {"file_path": str(WS / "warehouse/README.md")}, False),
    ("Read", {"file_path": "warehouse/README.md"}, False),
    ("Read", {"file_path": str(paths.ROOT / "benchmark/products/a/spec.yaml")}, True),
    ("Glob", {"pattern": "**/*.yml", "path": "../.."}, True),
    ("Bash", {"command": f"cd {WS}/warehouse && dbt build"}, False),
    ("Bash", {"command": "factory validate spec output/spec.yaml"}, False),
    ("Bash", {"command": "select 1 -- a..b"}, False),
    ("Bash", {"command": f"cd {WS} && factory validate spec output/spec.yaml"}, False),
    ("Bash", {"command": f"{paths.ROOT}/.venv/bin/factory validate spec {WS}/output/spec.yaml"}, False),
    ("Bash", {"command": f"cd {paths.ROOT} && cat benchmark/products/x/spec.yaml"}, True),
    ("Bash", {"command": "cat ../../benchmark/products/x/spec.yaml"}, True),
    ("Bash", {"command": f"ls {paths.ROOT}-oracle"}, True),
    ("Bash", {"command": "ls ~/anything"}, True),
    ("Bash", {"command": "cd && ls"}, True),
])
def test_workspace_guard(tool, args, escapes):
    assert (_escapes(WS, tool, args) is not None) == escapes
