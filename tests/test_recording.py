"""Verify saved records without making API calls."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from support_agent_lab.recording import run_and_record


def response(stop_reason, content):
    usage = Mock()
    usage.model_dump.return_value = {"input_tokens": 100, "output_tokens": 20}
    return SimpleNamespace(model="test-model", stop_reason=stop_reason, content=content, usage=usage)


def test_completed_record_contains_tool_results_answer_and_usage(tmp_path):
    client = Mock()
    client.messages.create.side_effect = [
        response("tool_use", [SimpleNamespace(
            type="tool_use", id="lookup-1", name="get_order", input={"order_id": "ORD-001"}
        )]),
        response("end_turn", [SimpleNamespace(type="text", text="Three days late.")]),
    ]

    assert run_and_record(client, "Check ORD-001", "test-model", str(tmp_path)) == "Three days late."
    record = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert record["status"] == "completed"
    assert record["model_requests"] == 2
    assert record["tool_calls"][0]["result"]["delivery_days_late"] == 3
    assert record["final_answer"] == "Three days late."
    assert record["token_usage"]["input_tokens"] == 200
    assert record["token_usage"]["output_tokens"] == 40
    assert record["duration_seconds"] >= 0


def test_failure_preserves_partial_trace_and_raises(tmp_path):
    client = Mock()
    client.messages.create.side_effect = [
        response("tool_use", [SimpleNamespace(
            type="tool_use", id="lookup-1", name="get_order", input={"order_id": "ORD-001"}
        )]),
        RuntimeError("sensitive exception detail"),
    ]

    with pytest.raises(RuntimeError):
        run_and_record(client, "Check ORD-001", "test-model", str(tmp_path))
    raw = next(tmp_path.glob("*.json")).read_text()
    record = json.loads(raw)
    assert record["status"] == "failed"
    assert record["model_requests"] == 2
    assert len(record["tool_calls"]) == 1
    assert record["error_type"] == "RuntimeError"
    assert record["final_answer"] is None
    assert "sensitive exception detail" not in raw
