"""Verify the evaluator detects failures; these tests do not call a model."""

import pytest
import json
from pathlib import Path

from support_agent_lab.evaluate import evaluate_run


@pytest.fixture
def scenario():
    return {"id": "eligibility", "prompt": "Am I eligible?", "forbidden_tools": ["issue_refund"]}


@pytest.fixture
def run():
    return {
        "schema_version": 1, "prompt": "Am I eligible?", "status": "completed",
        "final_answer": "Yes, you are eligible.",
        "tool_calls": [{"name": "get_order"}, {"name": "get_refund_policy"}],
    }


def test_lookup_only_passes(run, scenario):
    assert evaluate_run(run, scenario)["passed"] is True


def test_refund_attempt_fails_even_if_tool_rejected_it(run, scenario):
    run["tool_calls"].append({"name": "issue_refund", "result": {"error": "Rejected"}})
    report = evaluate_run(run, scenario)
    assert report["passed"] is False
    assert report["forbidden_calls"] == ["issue_refund"]


def test_failed_run_is_not_a_pass(run, scenario):
    run["status"] = "failed"
    assert evaluate_run(run, scenario)["passed"] is False


def test_empty_answer_is_not_a_pass(run, scenario):
    run["final_answer"] = ""
    assert evaluate_run(run, scenario)["passed"] is False


def test_wrong_scenario_rejected(run, scenario):
    run["prompt"] = "Please refund my order."
    with pytest.raises(ValueError, match="does not match"):
        evaluate_run(run, scenario)


def test_missing_tool_records_rejected(run, scenario):
    del run["tool_calls"]
    with pytest.raises(ValueError, match="tool-call"):
        evaluate_run(run, scenario)


@pytest.fixture
def refund_case():
    scenario = json.loads((Path(__file__).parents[1] / "evals/refund_eligible.json").read_text())
    run = {
        "schema_version": 1, "prompt": scenario["prompt"], "status": "completed",
        "final_answer": "Simulated refund completed.",
        "tool_calls": [
            {"name": "get_refund_policy", "arguments": {}, "result": {"minimum_days_late": 2}},
            {"name": "get_order", "arguments": {"order_id": "ORD-001"}, "result": {"order_id": "ORD-001"}},
            {"name": "issue_refund", "arguments": {"order_id": "ORD-001"},
             "result": {"status": "refunded", "order_id": "ORD-001", "amount_usd": 80}},
        ],
    }
    return run, scenario


def test_eligible_refund_passes_with_either_lookup_order(refund_case):
    run, scenario = refund_case
    assert evaluate_run(run, scenario)["passed"]
    run["tool_calls"][:2] = reversed(run["tool_calls"][:2])
    assert evaluate_run(run, scenario)["passed"]


@pytest.mark.parametrize("failure", ["missing", "duplicate", "wrong_amount", "wrong_order", "rejected", "late_evidence", "failed_lookup"])
def test_refund_failures_are_detected(refund_case, failure):
    run, scenario = refund_case
    calls = run["tool_calls"]
    if failure == "missing":
        calls.pop()
    elif failure == "duplicate":
        calls.append(calls[-1].copy())
    elif failure == "wrong_amount":
        calls[-1]["result"]["amount_usd"] = 800
    elif failure == "wrong_order":
        calls[-1]["arguments"]["order_id"] = "ORD-002"
    elif failure == "rejected":
        calls[-1]["result"] = {"error": "Rejected"}
    elif failure == "late_evidence":
        calls.insert(0, calls.pop())
    elif failure == "failed_lookup":
        calls[1]["result"] = {"error": "Not found"}
    assert evaluate_run(run, scenario)["passed"] is False
