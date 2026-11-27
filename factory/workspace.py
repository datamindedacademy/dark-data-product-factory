"""Every agent run works in its own folder, a workspace:

    <ws>/
      data/      the CSV files (a fresh copy per run)
      input/     what the station gets (issue.md, spec.json, feedback.md, ...)
      output/    what the station writes (spec.json, answers.json, review.json, ...)
"""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime
from pathlib import Path

from factory import paths


def new_run_id(prefix: str) -> str:
    return f"{datetime.now():%Y%m%d-%H%M%S}-{prefix}-{uuid.uuid4().hex[:6]}"


def create(run_dir: Path) -> Path:
    ws = run_dir / "workspace"
    shutil.copytree(paths.DATA, ws / "data")
    (ws / "input").mkdir()
    (ws / "output").mkdir()
    return ws
