#!/usr/bin/env bash
# Runs from the "Phoenix" task in .vscode/tasks.json when the folder opens, in the foreground of
# that terminal: every agent run becomes a trace at http://localhost:6006. (Started in the
# background from postStartCommand, Codespaces kills it.) Also `make phoenix` on a laptop.
if curl -fs -o /dev/null http://localhost:6006; then
  echo "Phoenix is already running at http://localhost:6006."
  exit 0
fi
echo "Starting Phoenix at http://localhost:6006 (log: /tmp/phoenix.log). Keep this terminal open."
uvx --python 3.13 --from arize-phoenix phoenix serve 2>&1 | tee /tmp/phoenix.log
