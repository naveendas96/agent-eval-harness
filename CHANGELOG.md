# Changelog

## Unreleased

- Added a "Run it in 60 seconds" section to the README (install, run baseline and candidate, then `aeh compare` which exits 1). The documented command now uses `python3` rather than `python3.11`.
- Added GitHub issue and pull request templates.
- Added tests for regex accuracy scoring, unscored cases, and rejection of an unknown adapter spec.

## 0.1.0 - 2026-10-14

Initial public release: YAML eval suites, mock/callable/HTTP adapters, deterministic scorers plus an optional LLM judge, SQLite run storage, run comparison with regression thresholds, and a Streamlit dashboard. The CI workflow lives under `examples/ci/` so it can be copied into `.github/workflows/` when wanted.
