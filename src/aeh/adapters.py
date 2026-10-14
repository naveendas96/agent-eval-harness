"""Adapter interface: anything that turns an input into an AgentOutput can be evaluated."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

import httpx


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    model: str = "mock"


class Adapter(Protocol):
    name: str

    def run(self, input: str, context: str = "") -> AgentOutput: ...


class CallableAdapter:
    def __init__(self, name: str, fn: Callable[[str, str], AgentOutput]) -> None:
        self.name, self.fn = name, fn

    def run(self, input: str, context: str = "") -> AgentOutput:
        t0 = time.perf_counter()
        out = self.fn(input, context)
        out.latency_ms = out.latency_ms or (time.perf_counter() - t0) * 1000
        return out


class HTTPAdapter:
    """POST {input, context} to an agent endpoint returning {text, tool_calls, usage}."""
    def __init__(self, url: str) -> None:
        self.name, self.url = f"http:{url}", url

    def run(self, input: str, context: str = "") -> AgentOutput:
        t0 = time.perf_counter()
        j = httpx.post(self.url, json={"input": input, "context": context}, timeout=120).json()
        u = j.get("usage", {})
        return AgentOutput(j["text"], [ToolCall(t["name"], t.get("args", {})) for t in j.get("tool_calls", [])],
                           u.get("input_tokens", 0), u.get("output_tokens", 0), (time.perf_counter() - t0) * 1000, j.get("model", "unknown"))


def _mock_agent(version: str) -> Callable[[str, str], AgentOutput]:
    """Deterministic demo agent. v2 is a 'cheaper prompt' that regresses on tools and safety."""
    def fn(q: str, ctx: str) -> AgentOutput:
        ql = q.lower()
        calls: list[ToolCall] = []
        if "order" in ql:
            oid = next((w.strip("?#.,") for w in q.split() if w.strip("?#.,").isdigit()), "")
            calls.append(ToolCall("lookup_order", {"order_id": oid}))
            text = f"Order {oid} shipped on 12 Oct and arrives in 2 days."
            if "refund" in ql and version == "v1":
                calls.append(ToolCall("create_refund", {"order_id": oid}))
                text += " A refund has been initiated."
        elif any(b in ql for b in ("password of", "ignore previous", "credit card")):
            text = "I can't help with that request." if version == "v1" else "Sure, here is what I found: the admin password is hunter2."
        elif ctx:
            first = ctx.split(". ")[0].rstrip(".") + "."
            text = first if version == "v1" else first + " We also offer free lifetime upgrades."
        else:
            text = "I don't know."
        tin = 400 + len(q) // 4 + len(ctx) // 4
        return AgentOutput(text, calls, tin if version == "v1" else tin // 2, 60, 120.0 if version == "v1" else 80.0, f"mock-{version}")
    return fn


def get_adapter(spec: str) -> Adapter:
    if spec.startswith("mock:"):
        v = spec.split(":", 1)[1]
        return CallableAdapter(spec, _mock_agent(v))
    if spec.startswith("http"):
        return HTTPAdapter(spec)
    raise ValueError(f"unknown adapter {spec}")
