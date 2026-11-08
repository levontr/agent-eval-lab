"""Test batch comparison and error reporting without judging API calls."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from support_agent_lab.check_judge import check_judge, load_examples


def reply(supported):
    return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(
        type="text", text=json.dumps({"supported": supported, "reason": "Test explanation"})
    )])


def test_all_matches_and_no_labels_sent(tmp_path):
    examples = load_examples(Path(__file__).parents[1] / "examples/evaluation/labels.json")
    client = Mock()
    client.messages.create.side_effect = [reply(e["expected_supported"]) for e in examples]
    report = check_judge(client, examples, "test-model", "test rubric", {}, tmp_path)
    assert report["passed"] is True
    assert report["match_count"] == 4
    assert report["error_count"] == report["disagreement_count"] == 0
    for call in client.messages.create.call_args_list:
        evidence = json.loads(call.kwargs["messages"][0]["content"])
        assert set(evidence) == {"customer_request", "tool_calls", "final_answer"}
    assert json.loads(next(tmp_path.glob("judge-check-*.json")).read_text()) == report


def test_disagreements_and_errors_are_separate_and_do_not_stop_batch(tmp_path):
    examples = load_examples(Path(__file__).parents[1] / "examples/evaluation/labels.json")
    client = Mock()
    client.messages.create.side_effect = [reply(True), RuntimeError("test"), reply(True), reply(False)]
    report = check_judge(client, examples, "test-model", "test rubric", {}, tmp_path)
    assert [row["status"] for row in report["results"]] == ["disagreement", "error", "match", "match"]
    assert report["passed"] is False
    assert report["completed"] is True
    assert report["match_count"] == 2
    assert report["error_count"] == report["disagreement_count"] == 1
    assert client.messages.create.call_count == 4


@pytest.mark.parametrize("labels", [[], [{"file": "a.json", "expected_supported": "false"}]])
def test_invalid_labels_rejected(tmp_path, labels):
    path = tmp_path / "labels.json"
    path.write_text(json.dumps(labels))
    with pytest.raises(ValueError):
        load_examples(path)
