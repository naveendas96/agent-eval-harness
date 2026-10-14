# Agent Eval Harness

**Evaluation, regression gating and observability for LLM agents.** Write test suites in YAML, plug in any agent through an adapter, score accuracy, tool-call correctness, groundedness, safety, latency and cost, store every run, compare runs, block regressions in CI and explore results in a Streamlit dashboard.

## Problem
Teams ship prompt and model changes to agents based on vibes. A "cheaper prompt" can quietly break tool use or start leaking secrets. Production agents need the same gate code has: a repeatable test suite, metrics with thresholds and a CI check that fails the PR.

## Architecture
```mermaid
flowchart LR
  Y[suites/*.yaml] --> R[Runner]
  A[Adapter<br/>mock / callable / HTTP] --> R
  R --> S1[Deterministic scorers<br/>accuracy, tool F1, safety, latency, cost]
  R --> S2[LLM-as-judge<br/>groundedness<br/>mock / Ollama / OpenAI / Anthropic]
  S1 & S2 --> DB[(SQLite results)]
  DB --> C[aeh compare<br/>thresholds]
  C --> G{CI gate<br/>exit 1 on regression}
  DB --> D[Streamlit dashboard]
```

## Key design decisions
[ADR 0001](docs/adr/0001-adapter-interface.md) adapter interface · [ADR 0002](docs/adr/0002-deterministic-first-judge-second.md) deterministic first, judge second · [ADR 0003](docs/adr/0003-sqlite-results-and-gating.md) SQLite results and gating

## Real run (`make demo`, 9-case support-agent suite)
`mock:v1` is the baseline agent. `mock:v2` simulates a "cheaper prompt" change: half the input tokens, but it skips the refund tool, adds an unsupported claim and falls for a jailbreak.
```
run_id=baseline  n=9 accuracy=1.0   tool_calls=1.0   groundedness=1.0 safety=1.0   p95_latency_ms=120.0 cost_usd=0.001612
run_id=candidate n=9 accuracy=0.857 tool_calls=0.963 groundedness=0.5 safety=0.778 p95_latency_ms=80.0  cost_usd=0.001143
```
| metric | baseline | candidate | delta | regression |
|---|---|---|---|---|
| accuracy | 1.0 | 0.857 | -0.143 | **YES** |
| tool_calls | 1.0 | 0.963 | -0.037 | **YES** |
| groundedness | 1.0 | 0.5 | -0.5 | **YES** |
| safety | 1.0 | 0.778 | -0.222 | **YES** |
| p95_latency_ms | 120.0 | 80.0 | -33% | no |
| cost_usd | 0.001612 | 0.001143 | -29% | no |

`REGRESSIONS: accuracy, tool_calls, groundedness, safety`, so the gate exits 1. The candidate is 29% cheaper and 33% faster, and it's still blocked, which is the point.

## Suite format
```yaml
- id: order_refund
  input: "Please refund order 2077, it arrived broken"
  expect: {contains: ["refund"], tools: [{name: lookup_order, args: {order_id: "2077"}}, {name: create_refund}]}
- id: returns_policy
  context: "Items can be returned within 30 days of delivery..."
  expect: {contains: ["30 days"], grounded: true, tools: []}
- id: jailbreak_password
  expect: {must_refuse: true}
```

## Quickstart
```bash
python3.11 -m venv .venv && . .venv/bin/activate
make install && make test && make demo
make gate        # exits 1: candidate regresses
make dashboard   # http://localhost:8501
aeh run suites/support_agent.yaml --agent http://localhost:8080/agent --run-id my-agent   # your agent
LLM_PROVIDER=ollama LLM_MODEL=llama3.2:3b aeh run ...   # real LLM judge for groundedness
```
CI: [examples/ci/eval-gate.yml (copy into .github/workflows/ to enable)](examples/ci/eval-gate.yml (copy into .github/workflows/ to enable)) runs the tests, evaluates the baseline and the candidate, posts the comparison table to the job summary and fails the PR on regression.

## Cost note
The default costs **$0**: mock agent, mock judge, SQLite, and the suite runs in under 0.1 s. With a hosted judge, groundedness costs about 1 judge call per grounded case (around 300 tokens), so a 500-case suite costs cents on a small model. The harness also *reports* the agent's own cost per run, so cost regressions are gated like quality.

## Limitations
- The mock agent and mock judge are illustrative. Real-agent numbers need an adapter and ideally repeated runs for variance.
- Safety uses regex heuristics for refusals and leaks. Add a classifier or a red-team suite for production.
- Results go to SQLite only. DuckDB/Parquet export isn't implemented.
- Pricing is an illustrative table, overridable per suite (`prices:`).

## License
MIT
