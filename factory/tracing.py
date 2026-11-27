"""Turn an Agno run into a JSONL trace + a run summary.

Every run of every agent writes ``trace.jsonl`` and ``summary.json`` in its run
directory. The benchmark adds scores to the summary, and a line manager
could read traces from many runs - so keep this format stable.

trace.jsonl event types::

    {"type": "reasoning", "turn": n, "text": "..."}            when the model reasons (effort=...)
    {"type": "assistant_text", "turn": n, "chars": n, "text": "..."}
    {"type": "tool_use", "turn": n, "id": ..., "name": "Bash", "input": {...}}
    {"type": "tool_result", "turn": n, "id": ..., "name": "Bash", "is_error": bool, "chars": n, "preview": "..."}
    {"type": "result", "subtype": "success", "num_turns": n, "duration_ms": n, "total_cost_usd": x, "usage": {...}}
"""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PREVIEW = 600

def _trim(v: Any, n: int = 2000) -> Any:
    if isinstance(v, str):
        return v if len(v) <= n else v[:n] + f"…[{len(v) - n} chars]"
    if isinstance(v, dict):
        return {k: _trim(x, n) for k, x in v.items()}
    if isinstance(v, list):
        return [_trim(x, n) for x in v[:50]]
    return v


def _result_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in content)
    return "" if content is None else str(content)


@dataclass
class Tracer:
    run_dir: Path
    meta: dict[str, Any]
    turn: int = 0
    tool_counts: Counter = field(default_factory=Counter)
    tool_errors: Counter = field(default_factory=Counter)
    result: dict[str, Any] = field(default_factory=dict)
    final_text: str = ""
    started: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._f = (self.run_dir / "trace.jsonl").open("w")

    def _emit(self, event: dict[str, Any]) -> None:
        event = {"t": round(time.time() - self.started, 2), **event}
        self._f.write(json.dumps(event, default=str) + "\n")
        self._f.flush()

    def on_agno_run(self, out: Any, model: str) -> None:
        """The same events from an Agno ``RunOutput``. Written after the run, so every ``t`` is the end time.

        ``model`` (from agent.yaml) prices the run when the RunOutput does not name the model it used.
        """
        for m in out.messages or []:
            if m.role == "assistant":
                self.turn += 1
                if getattr(m, "reasoning_content", None):
                    self._emit({"type": "reasoning", "turn": self.turn, "text": _trim(m.reasoning_content)})
                if isinstance(m.content, str) and m.content.strip():
                    self.final_text = m.content
                    self._emit({"type": "assistant_text", "turn": self.turn, "chars": len(m.content), "text": _trim(m.content)})
                elif not m.tool_calls:  # the model said nothing and called nothing: the run ends here
                    reasoning = getattr(m, "reasoning_content", None) or ""
                    self._emit({"type": "assistant_empty", "turn": self.turn, "reasoning": _trim(reasoning)})
            elif m.role == "tool":
                name, text = m.tool_name or "?", _result_text(m.content)
                self.tool_counts[name] += 1
                self._emit({"type": "tool_use", "turn": self.turn, "id": m.tool_call_id, "name": name, "input": _trim(m.tool_args)})
                if m.tool_call_error:
                    self.tool_errors[name] += 1
                self._emit({"type": "tool_result", "turn": self.turn, "id": m.tool_call_id, "name": name,
                            "is_error": bool(m.tool_call_error), "chars": len(text), "preview": text[:PREVIEW]})
        mt = out.metrics
        usage = {"input_tokens": mt.input_tokens, "output_tokens": mt.output_tokens,
                 "cache_read_input_tokens": mt.cache_read_tokens, "cache_creation_input_tokens": mt.cache_write_tokens} if mt else {}
        status = str(getattr(out.status, "value", out.status)).lower()
        self.result = {"subtype": status, "is_error": status != "completed", "num_turns": self.turn,
                       "total_cost_usd": mt.cost if mt else None,  # what OpenRouter charged
                       "usage": usage}
        self._emit({"type": "result", **self.result})

    def close(self, error: str | None = None) -> dict[str, Any]:
        if error:
            self._emit({"type": "error", "error": error})
        self._f.close()
        usage = self.result.get("usage") or {}
        summary = {
            **self.meta,
            "status": "error" if (error or self.result.get("is_error")) else "ok",
            "error": error,
            "result_subtype": self.result.get("subtype"),
            "num_turns": self.result.get("num_turns", self.turn),
            "duration_ms": self.result.get("duration_ms", int((time.time() - self.started) * 1000)),
            "total_cost_usd": self.result.get("total_cost_usd"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
            "tool_calls": dict(self.tool_counts),
            "tool_errors": dict(self.tool_errors),
            "final_text": self.final_text[-2000:],
        }
        (self.run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
        return summary
