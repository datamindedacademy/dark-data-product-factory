"""Turn the Agent SDK message stream (or an Agno run) into a JSONL trace + a run summary.

Every run of every agent writes ``trace.jsonl`` and ``summary.json`` in its run
directory. The benchmark adds scores to the summary, and the line-manager agent
reads traces from many runs to find bottlenecks - so keep this format stable.

trace.jsonl event types::

    {"type": "init", "model": ..., "tools": [...], "skills": [...]}
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

from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from factory.llm import via_openrouter

PREVIEW = 600

# USD per million tokens (input, output), matched on the model id. Agno does not report cost for
# Claude, so Agno runs are priced from their token counts. Source: Anthropic price list, 2026-11.
# ponytail: three hard-coded prices; an unknown model gets cost None (scored as the worst cost in
# the competition) - add a row when you allow another model.
PRICES = {"opus-5-5": (4.0, 20.0), "sonnet-5-5": (2.0, 10.0), "haiku-5-5": (0.1, 0.5)}


def estimate_cost(model: str, usage: dict[str, Any]) -> float | None:
    """Cost from token counts: cache writes at 1.25x and cache reads at 0.05x the input price."""
    price = next((p for k, p in PRICES.items() if k in (model or "").replace(".", "-")), None)
    if not price:
        return None
    n = lambda k: usage.get(k) or 0  # noqa: E731
    inp = n("input_tokens") + 1.25 * n("cache_creation_input_tokens") + 0.05 * n("cache_read_input_tokens")
    return round((inp * price[0] + n("output_tokens") * price[1]) / 1e6, 4)


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
    tool_names: dict[str, str] = field(default_factory=dict)
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

    def on_message(self, msg: Any) -> None:
        if isinstance(msg, SystemMessage) and msg.subtype == "init":
            d = msg.data
            self._emit({"type": "init", "model": d.get("model"), "tools": d.get("tools"),
                        "skills": d.get("skills"), "mcp_servers": d.get("mcp_servers")})
        elif isinstance(msg, AssistantMessage):
            self.turn += 1
            for b in msg.content:
                if isinstance(b, TextBlock) and b.text.strip():
                    self.final_text = b.text
                    self._emit({"type": "assistant_text", "turn": self.turn, "chars": len(b.text), "text": _trim(b.text)})
                elif isinstance(b, ToolUseBlock):
                    self.tool_names[b.id] = b.name
                    self.tool_counts[b.name] += 1
                    self._emit({"type": "tool_use", "turn": self.turn, "id": b.id, "name": b.name, "input": _trim(b.input)})
        elif isinstance(msg, UserMessage) and isinstance(msg.content, list):
            for b in msg.content:
                if isinstance(b, ToolResultBlock):
                    name = self.tool_names.get(b.tool_use_id, "?")
                    text = _result_text(b.content)
                    if b.is_error:
                        self.tool_errors[name] += 1
                    self._emit({"type": "tool_result", "turn": self.turn, "id": b.tool_use_id, "name": name,
                                "is_error": bool(b.is_error), "chars": len(text), "preview": text[:PREVIEW]})
        elif isinstance(msg, ResultMessage):
            self.result = {"subtype": msg.subtype, "is_error": msg.is_error, "num_turns": msg.num_turns,
                           "duration_ms": msg.duration_ms,
                           # through OpenRouter the SDK's own figure is not Anthropic's price list: count tokens
                           "total_cost_usd": estimate_cost(self.meta.get("model"), msg.usage or {}) if via_openrouter()
                           else msg.total_cost_usd,
                           "usage": msg.usage, "stop_reason": msg.stop_reason}
            self._emit({"type": "result", **self.result})

    def on_agno_run(self, out: Any, model: str) -> None:
        """The same events from an Agno ``RunOutput``. Written after the run, so every ``t`` is the end time.

        ``model`` (from agent.yaml) prices the run when the RunOutput does not name the model it used.
        """
        for m in out.messages or []:
            if m.role == "assistant":
                self.turn += 1
                if isinstance(m.content, str) and m.content.strip():
                    self.final_text = m.content
                    self._emit({"type": "assistant_text", "turn": self.turn, "chars": len(m.content), "text": _trim(m.content)})
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
                       "total_cost_usd": (mt.cost if mt else None) or estimate_cost(getattr(out, "model", None) or model, usage),
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
