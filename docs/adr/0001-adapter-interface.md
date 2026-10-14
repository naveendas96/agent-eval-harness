# ADR 0001: Evaluate agents through a minimal adapter interface
**Decision:** `Adapter.run(input, context) -> AgentOutput(text, tool_calls, tokens_in, tokens_out, latency_ms, model)`. There are built-in mock, Python-callable and HTTP adapters.
**Why:** It decouples the harness from frameworks (LangGraph, CrewAI, custom). Any agent that exposes an endpoint can be gated.
