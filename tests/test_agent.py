"""Check the tool protocol offline; these do not evaluate a real model."""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from support_agent_lab.agent import execute_tool, run_agent
from support_agent_lab import store


def tool_response():
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[SimpleNamespace(type="tool_use", name="get_order", input={"order_id": "ORD-001"}, id="call-1")],
    )


def test_tool_result_is_sent_back_with_matching_id():
    client = Mock()
    client.messages.create.side_effect = [
        tool_response(),
        SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Your order was 3 days late.")]),
    ]

    assert run_agent(client, "Check ORD-001", "test-model") == "Your order was 3 days late."
    messages = client.messages.create.call_args.kwargs["messages"]
    result = messages[-1]["content"][0]
    assert result["tool_use_id"] == "call-1"
    assert json.loads(result["content"])["delivery_days_late"] == 3
    assert result["is_error"] is False


def test_repeating_model_stops_at_call_limit():
    client = Mock()
    client.messages.create.side_effect = [tool_response() for _ in range(5)]

    with pytest.raises(RuntimeError, match="limit of 5"):
        run_agent(client, "Check ORD-001", "test-model")
    assert client.messages.create.call_count == 5


def test_truncated_response_is_not_returned_as_success():
    client = Mock()
    client.messages.create.return_value = SimpleNamespace(stop_reason="max_tokens", content=[])

    with pytest.raises(RuntimeError, match="max_tokens"):
        run_agent(client, "Check ORD-001", "test-model")


@pytest.mark.parametrize(("name", "arguments"), [
    ("unknown", {}),
    ("get_refund_policy", {"order_id": "ORD-001"}),
    ("issue_refund", {"order_id": 1}),
    ("issue_refund", {"order_id": "ORD-001", "amount": 1000}),
])
def test_invalid_tool_requests_do_not_change_store(name, arguments):
    before = deepcopy(store.ORDERS)
    assert "error" in execute_tool(name, arguments)
    assert store.ORDERS == before


def test_refund_workflow_executes_tools_and_returns_results(monkeypatch):
    monkeypatch.setattr(store, "ORDERS", deepcopy(store.ORDERS))
    client = Mock()
    responses = []
    for index, (name, arguments) in enumerate([
        ("get_order", {"order_id": "ORD-001"}),
        ("get_refund_policy", {}),
        ("issue_refund", {"order_id": "ORD-001"}),
    ]):
        responses.append(SimpleNamespace(stop_reason="tool_use", content=[
            SimpleNamespace(type="tool_use", name=name, input=arguments, id=f"call-{index}")
        ]))
    responses.append(SimpleNamespace(stop_reason="end_turn", content=[
        SimpleNamespace(type="text", text="Simulated refund complete.")
    ]))
    client.messages.create.side_effect = responses

    assert run_agent(client, "Please refund ORD-001 if eligible", "test-model") == "Simulated refund complete."
    assert store.get_order("ORD-001")["refunded"] is True
    messages = client.messages.create.call_args.kwargs["messages"]
    results = [message["content"][0] for message in messages[2::2]]
    assert [result["tool_use_id"] for result in results] == ["call-0", "call-1", "call-2"]
    assert json.loads(results[1]["content"])["minimum_days_late"] == 2
    assert json.loads(results[2]["content"])["amount_usd"] == 80
    assert all(result["is_error"] is False for result in results)
