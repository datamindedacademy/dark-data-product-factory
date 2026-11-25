#!/usr/bin/env bash
# Runs once, when the codespace is created. Every step runs even if an earlier one fails,
# and the summary at the end names what failed.
set -u
cd "$(dirname "$0")/.."

failed=()
step() {
  echo "==> $1"
  shift
  "$@" || failed+=("$*")
}

step "dependencies (Python 3.15)" uv sync --python 3.15 --extra dev
step "warehouse" .venv/bin/factory setup
step "Phoenix" uvx --python 3.13 --from arize-phoenix phoenix --help
step "opencode" bash -c "curl -fsSL https://opencode.ai/v2/install | bash"

if [ ${#failed[@]} -gt 0 ]; then
  echo
  echo "These setup steps failed; rerun them by hand:"
  printf '  %s\n' "${failed[@]}"
  exit 1
fi
echo "Setup done."
