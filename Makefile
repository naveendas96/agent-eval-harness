.PHONY: install test demo gate dashboard
install: ; pip install -e ".[dev,dashboard]"
test: ; pytest -q
demo:
	aeh run suites/support_agent.yaml --agent mock:v1 --run-id baseline
	aeh run suites/support_agent.yaml --agent mock:v2 --run-id candidate
	aeh compare baseline candidate
gate: ; aeh compare baseline candidate --fail-on-regression
dashboard: ; streamlit run src/aeh/dashboard.py
