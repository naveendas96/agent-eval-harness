"""Run a YAML suite against an adapter and persist results to SQLite."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

from . import scorers
from .adapters import Adapter

DB = Path("results/evals.sqlite")
METRICS = ["accuracy", "tool_calls", "groundedness", "safety"]


def connect(db: Path = DB) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.execute("""CREATE TABLE IF NOT EXISTS results(run_id TEXT, suite TEXT, agent TEXT, case_id TEXT, ts REAL,
        accuracy REAL, tool_calls REAL, groundedness REAL, safety REAL, latency_ms REAL, cost_usd REAL, output TEXT,
        PRIMARY KEY(run_id, case_id))""")
    return con


def run_suite(suite_path: str, adapter: Adapter, run_id: str, db: Path = DB) -> dict[str, Any]:
    suite = yaml.safe_load(Path(suite_path).read_text())
    con = connect(db)
    con.execute("DELETE FROM results WHERE run_id=?", (run_id,))
    rows = []
    for c in suite["cases"]:
        out = adapter.run(c["input"], c.get("context", ""))
        exp = c.get("expect", {})
        s = {"accuracy": scorers.accuracy(out, exp), "tool_calls": scorers.tool_calls(out, exp),
             "groundedness": scorers.groundedness(out, exp, c.get("context", "")), "safety": scorers.safety(out, exp),
             "latency_ms": out.latency_ms, "cost_usd": scorers.cost_usd(out, suite.get("prices"))}
        con.execute("INSERT INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (run_id, suite["name"], adapter.name, c["id"], time.time(), s["accuracy"], s["tool_calls"],
                     s["groundedness"], s["safety"], s["latency_ms"], s["cost_usd"], json.dumps({"text": out.text, "tools": [t.name for t in out.tool_calls]})))
        rows.append(s)
    con.commit()
    return summarize(con, run_id)


def summarize(con: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    cur = con.execute("SELECT accuracy, tool_calls, groundedness, safety, latency_ms, cost_usd FROM results WHERE run_id=?", (run_id,))
    cols = [d[0] for d in cur.description]
    data = [dict(zip(cols, r)) for r in cur.fetchall()]
    if not data:
        raise KeyError(f"no such run {run_id}")
    out: dict[str, Any] = {"run_id": run_id, "n": len(data)}
    for m in METRICS:
        vals = [d[m] for d in data if d[m] is not None]
        out[m] = round(mean(vals), 3) if vals else None
    lat = sorted(d["latency_ms"] for d in data)
    out["p95_latency_ms"] = round(lat[min(len(lat) - 1, int(0.95 * len(lat)))], 1)
    out["cost_usd"] = round(sum(d["cost_usd"] for d in data), 6)
    return out
