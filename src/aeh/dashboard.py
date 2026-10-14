"""Streamlit dashboard: `streamlit run src/aeh/dashboard.py`."""
import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Agent Eval Harness", layout="wide")
st.title("Agent Eval Harness")
con = sqlite3.connect("results/evals.sqlite")
df = pd.read_sql("SELECT * FROM results", con)
if df.empty:
    st.info("No runs yet. Run `make demo`.")
    st.stop()
metrics = ["accuracy", "tool_calls", "groundedness", "safety"]
summary = df.groupby("run_id").agg({**{m: "mean" for m in metrics}, "latency_ms": "median", "cost_usd": "sum", "ts": "max"}).sort_values("ts")
st.subheader("Runs")
st.dataframe(summary.drop(columns="ts").style.format(precision=3), use_container_width=True)
st.bar_chart(summary[metrics])
runs = list(summary.index)
c1, c2 = st.columns(2)
base = c1.selectbox("Baseline", runs, index=0)
cand = c2.selectbox("Candidate", runs, index=len(runs) - 1)
m = df[df.run_id == base].set_index("case_id")[metrics].join(df[df.run_id == cand].set_index("case_id")[metrics], lsuffix="_base", rsuffix="_cand")
st.subheader("Per-case diff")
st.dataframe(m, use_container_width=True)
st.subheader("Outputs")
st.dataframe(df[df.run_id.isin([base, cand])][["run_id", "case_id", "output"]], use_container_width=True)
