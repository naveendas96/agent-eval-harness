# ADR 0003: Results in SQLite, regression gating by per-metric thresholds
**Decision:** One row per (run, case) in `results/evals.sqlite` (stdlib, no server). `aeh compare` flags a regression when a quality metric drops by more than its threshold (safety tolerance is 0) or when p95 latency or cost rises by more than 25%. `--fail-on-regression` exits 1 to block CI.
**Why:** Quality, safety, latency and cost are traded off explicitly, so a cheaper model that leaks secrets can't pass.
**Consequences:** Small suites are noisy. Use repeats or wider thresholds for stochastic agents.
