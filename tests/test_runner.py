"""Exercise the whole suite over fake HTTP, without spending API credits."""

from copy import deepcopy
import json
from pathlib import Path

from anthropic import Anthropic
import httpx2
import pytest

from support_agent_lab import store
from support_agent_lab.runner import load_scenarios, run_suite


@pytest.mark.parametrize("fail_first", [False, True])
def test_suite_records_evaluates_resets_and_continues(tmp_path, monkeypatch, fail_first):
    scenarios = load_scenarios(Path(__file__).parents[1] / "evals")
    # Put the refund before the eligibility inquiry to catch state leakage.
    scenarios.sort(key=lambda scenario: "expected_refund" not in scenario)
    original = deepcopy(store.INITIAL_ORDERS)
    original["ORD-001"]["refunded"] = True
    monkeypatch.setattr(store, "ORDERS", original)
    started = []

    def handle(request):
        body = json.loads(request.content)
        prompt = body["messages"][0]["content"]
        turn = (len(body["messages"]) - 1) // 2
        if turn == 0:
            started.append(prompt)
            assert store.get_order("ORD-001")["refunded"] is False
            if fail_first and len(started) == 1:
                store.issue_refund("ORD-001")  # Failure must not leak partial state.
                return httpx2.Response(500, json={"type": "error", "error": {"type": "api_error", "message": "Test failure"}})
        order_id = "ORD-002" if "ORD-002" in prompt else "ORD-001"
        actions = [("get_refund_policy", {}), ("get_order", {"order_id": order_id})]
        if prompt.startswith("Please refund ORD-001"):
            actions.append(("issue_refund", {"order_id": order_id}))
        if turn < len(actions):
            name, arguments = actions[turn]
            content = [{"type": "tool_use", "id": f"call-{turn}", "name": name, "input": arguments}]
            stop = "tool_use"
        else:
            content = [{"type": "text", "text": "Finished the requested checks."}]
            stop = "end_turn"
        return httpx2.Response(200, json={
            "id": "msg-test", "type": "message", "role": "assistant",
            "model": body["model"], "content": content, "stop_reason": stop,
            "stop_sequence": None, "usage": {"input_tokens": 100, "output_tokens": 20},
        })

    with Anthropic(api_key="test-placeholder", max_retries=0,
                   http_client=httpx2.Client(transport=httpx2.MockTransport(handle))) as client:
        report = run_suite(client, scenarios, "claude-haiku-5-5", tmp_path)
    assert len(started) == 3
    assert report["passed_count"] == (2 if fail_first else 3)
    assert report["passed"] is (not fail_first)
    assert store.ORDERS is original
    assert original["ORD-001"]["refunded"] is True
    report_path = next(tmp_path.glob("experiment-*/report.json"))
    assert json.loads(report_path.read_text()) == report
    for result in report["results"]:
        assert (report_path.parent / result["run_file"]).exists()
        assert (report_path.parent / result["run_file"]).with_suffix(".otel.jsonl").exists()


def test_empty_dataset_rejected(tmp_path):
    with pytest.raises(ValueError, match="No scenario"):
        load_scenarios(tmp_path)


def test_duplicate_scenarios_rejected(tmp_path):
    scenario = {"id": "same", "prompt": "Check order", "forbidden_tools": []}
    for name in ("a.json", "b.json"):
        (tmp_path / name).write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match="unique"):
        load_scenarios(tmp_path)
