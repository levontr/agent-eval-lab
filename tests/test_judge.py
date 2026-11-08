"""Test request construction and validation, not model judgment quality."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from support_agent_lab.judge import judge_run


@pytest.fixture
def inputs():
    root = Path(__file__).parents[1]
    return (
        json.loads((root / "examples/evaluation/misleading_refund.json").read_text()),
        (root / "evals/judges/refund_outcome.prompt.txt").read_text(),
        json.loads((root / "evals/judges/refund_outcome.schema.json").read_text()),
    )


def client_with(text, stop="end_turn"):
    client = Mock()
    client.messages.create.return_value = SimpleNamespace(
        stop_reason=stop, content=[SimpleNamespace(type="text", text=text)]
    )
    return client


def test_sends_only_evidence_and_schema_without_tools_or_labels(inputs):
    run, rubric, schema = inputs
    run["expected_label"] = False
    client = client_with('{"supported": false, "reason": "No refund was executed."}')
    result = judge_run(client, run, "judge-model", rubric, schema)
    assert result["supported"] is False
    request = client.messages.create.call_args.kwargs
    assert request["system"] == rubric
    assert request["output_config"]["format"]["schema"] == schema
    evidence = json.loads(request["messages"][0]["content"])
    assert set(evidence) == {"customer_request", "tool_calls", "final_answer"}
    assert evidence["tool_calls"][1]["name"] == "get_order"
    assert "tools" not in request
    assert client.messages.create.call_count == 1


@pytest.mark.parametrize("text", [
    "not JSON", "[]", '{"supported": "false", "reason": "No evidence"}',
    '{"supported": true}', '{"supported": true, "reason": ""}',
    '{"supported": true, "reason": "OK", "extra": 1}',
])
def test_invalid_judgment_is_an_error(inputs, text):
    run, rubric, schema = inputs
    with pytest.raises(ValueError):
        judge_run(client_with(text), run, "judge-model", rubric, schema)


def test_truncated_response_is_not_a_judgment(inputs):
    run, rubric, schema = inputs
    with pytest.raises(ValueError, match="did not finish"):
        judge_run(client_with('{"supported": true, "reason": "OK"}', "max_tokens"), run, "judge-model", rubric, schema)


@pytest.mark.parametrize("field,value", [("status", "failed"), ("final_answer", ""), ("tool_calls", None)])
def test_invalid_evidence_rejected_before_api_call(inputs, field, value):
    run, rubric, schema = inputs
    run[field] = value
    client = Mock()
    with pytest.raises(ValueError):
        judge_run(client, run, "judge-model", rubric, schema)
    client.messages.create.assert_not_called()
