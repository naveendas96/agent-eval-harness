# ADR 0002: Deterministic scorers first, LLM-as-judge only where needed
**Decision:** Accuracy (contains/regex), tool-call F1 with argument matching, safety (refusal and leak regex), latency and cost are deterministic. Only groundedness uses a judge, and the judge is pluggable (`LLM_PROVIDER`), with a deterministic mock judge (sentence-level content-word support) as the default.
**Why:** Deterministic metrics are free, reproducible and can't be gamed by the judge's own biases. Judges are reserved for semantic properties.
**Consequences:** Judge scores from different providers aren't directly comparable. Pin the judge model per baseline.
