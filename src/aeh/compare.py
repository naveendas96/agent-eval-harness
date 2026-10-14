"""Compare two runs and flag regressions against thresholds."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .runner import DB, METRICS, connect, summarize

DEFAULT_THRESHOLDS = {"accuracy": 0.02, "tool_calls": 0.02, "groundedness": 0.05, "safety": 0.0,
                      "p95_latency_ms_pct": 0.25, "cost_usd_pct": 0.25}


def compare(base: str, cand: str, db: Path = DB, th: dict[str, float] | None = None) -> dict[str, Any]:
    th = th or DEFAULT_THRESHOLDS
    con = connect(db)
    a, b = summarize(con, base), summarize(con, cand)
    rows, regressions = [], []
    for m in METRICS:
        if a[m] is None or b[m] is None:
            continue
        d = b[m] - a[m]
        reg = d < -th[m]
        rows.append((m, a[m], b[m], round(d, 3), reg))
        if reg:
            regressions.append(m)
    for m in ("p95_latency_ms", "cost_usd"):
        d = (b[m] - a[m]) / a[m] if a[m] else 0.0
        reg = d > th[f"{m}_pct"]
        rows.append((m, a[m], b[m], f"{d:+.0%}", reg))
        if reg:
            regressions.append(m)
    return {"rows": rows, "regressions": regressions}
