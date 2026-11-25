"""Send every agent run to Phoenix, if it is running (the same setup as the agent evaluation course).

Start Phoenix in a second terminal (`make phoenix`), then open http://localhost:6006. Each agent
run becomes a trace with its model and tool calls. A benchmark or e2e run is one Phoenix session; stage, case and round are trace metadata.

If Phoenix is not running, nothing changes: `trace.jsonl` and `summary.json` are written either way.
"""

from __future__ import annotations

import os
import socket
from urllib.parse import urlparse

URL = os.getenv("PHOENIX_URL", "http://localhost:6006").rstrip("/")
_provider = None
_checked = False


def setup() -> bool:
    """Turn tracing on once, if Phoenix is reachable. Returns whether it is on."""
    global _provider, _checked
    if _checked:
        return _provider is not None
    _checked = True
    url = urlparse(URL)
    try:
        socket.create_connection((url.hostname, url.port or 80), timeout=0.5).close()
    except OSError:
        return False
    from openinference.instrumentation.agno import AgnoInstrumentor
    from phoenix.otel import register

    _provider = register(project_name=os.getenv("PHOENIX_PROJECT", "factory"), endpoint=f"{URL}/v1/traces",
                         batch=True, verbose=False)
    AgnoInstrumentor().instrument(tracer_provider=_provider)
    return True


def flush() -> None:
    if _provider is not None:
        _provider.force_flush()
