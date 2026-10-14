from pathlib import Path

from aeh.adapters import AgentOutput, ToolCall, get_adapter
from aeh.cli import main
from aeh.compare import compare
from aeh.llm import MockLLM
from aeh.runner import run_suite
from aeh import scorers

SUITE = str(Path(__file__).parents[1] / "suites" / "support_agent.yaml")


def test_tool_call_f1():
    out = AgentOutput("x", [ToolCall("lookup_order", {"order_id": "1"}), ToolCall("extra")])
    assert scorers.tool_calls(out, {"tools": [{"name": "lookup_order", "args": {"order_id": "1"}}]}) == 2 / 3
    assert scorers.tool_calls(AgentOutput("x"), {"tools": []}) == 1.0


def test_safety_detects_leak_and_refusal():
    assert scorers.safety(AgentOutput("I can't help with that request."), {"must_refuse": True}) == 1.0
    assert scorers.safety(AgentOutput("the admin password is x"), {"must_refuse": True}) == 0.0
    assert scorers.safety(AgentOutput("card 4111 1111 1111 1111"), {}) == 0.0


def test_mock_judge_groundedness():
    ctx = "Items can be returned within 30 days of delivery."
    assert scorers.groundedness(AgentOutput("Items can be returned within 30 days."), {"grounded": True}, ctx) == 1.0
    assert scorers.groundedness(AgentOutput("Items can be returned within 30 days. We offer free lifetime upgrades."), {"grounded": True}, ctx) == 0.5


def test_pluggable_judge():
    j = MockLLM(lambda p, s: 'verdict: {"score": 0.3, "reason": "partial"}')
    assert scorers.groundedness(AgentOutput("a"), {"grounded": True}, "ctx", judge=j) == 0.3


def test_cost():
    assert scorers.cost_usd(AgentOutput("x", tokens_in=1_000_000, tokens_out=0, model="unknown")) == 1.0


def test_baseline_perfect_and_regression_detected(tmp_path):
    db = tmp_path / "r.sqlite"
    a = run_suite(SUITE, get_adapter("mock:v1"), "a", db)
    assert a["accuracy"] == 1.0 and a["tool_calls"] == 1.0 and a["safety"] == 1.0
    run_suite(SUITE, get_adapter("mock:v2"), "b", db)
    r = compare("a", "b", db)
    assert {"accuracy", "tool_calls", "groundedness", "safety"} <= set(r["regressions"])
    assert "cost_usd" not in r["regressions"]  # v2 is cheaper
    assert compare("a", "a", db)["regressions"] == []


def test_cli_gate_exit_code(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["run", SUITE, "--agent", "mock:v1", "--run-id", "x"]) == 0
    assert main(["run", SUITE, "--agent", "mock:v2", "--run-id", "y"]) == 0
    assert main(["compare", "x", "y", "--fail-on-regression"]) == 1
    assert main(["compare", "x", "x", "--fail-on-regression"]) == 0
