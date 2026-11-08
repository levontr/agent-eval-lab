"""Use the real SDK with a fake HTTP transport: no API calls or credentials."""

import json

import httpx2
import pytest
from anthropic import Anthropic, InternalServerError
from openinference.instrumentation.anthropic import AnthropicInstrumentor

from support_agent_lab.recording import run_and_record


def test_real_sdk_creates_one_model_span_per_request_across_runs(tmp_path):
    requests = []

    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        first = len(body["messages"]) == 1
        return httpx2.Response(200, json={
            "id": "msg-test", "type": "message", "role": "assistant",
            "model": "claude-haiku-5-5", "stop_sequence": None,
            "stop_reason": "tool_use" if first else "end_turn",
            "content": [{"type": "tool_use", "id": "lookup-1", "name": "get_order", "input": {"order_id": "ORD-001"}}]
                if first else [{"type": "text", "text": "Three days late."}],
            "usage": {"input_tokens": 100, "output_tokens": 20},
        })

    with Anthropic(api_key="test-placeholder", max_retries=0,
                   http_client=httpx2.Client(transport=httpx2.MockTransport(handle))) as client:
        for _ in range(2):
            assert run_and_record(client, "Check ORD-001", "claude-haiku-5-5", str(tmp_path)) == "Three days late."
            assert not AnthropicInstrumentor().is_instrumented_by_opentelemetry

    assert len(requests) == 4
    for path in tmp_path.glob("*.otel.jsonl"):
        spans = [json.loads(line) for line in path.read_text().splitlines()]
        root = next(s for s in spans if s["attributes"].get("openinference.span.kind") == "AGENT")
        llms = [s for s in spans if s["attributes"].get("openinference.span.kind") == "LLM"]
        assert len(llms) == 2
        assert len([s for s in spans if s["attributes"].get("openinference.span.kind") == "TOOL"]) == 1
        for span in llms:
            assert span["parent_id"] == root["context"]["span_id"]
            assert span["context"]["trace_id"] == root["context"]["trace_id"]
            assert span["attributes"]["llm.token_count.prompt"] == 100
            assert span["attributes"]["llm.token_count.completion"] == 20
            assert span["attributes"]["llm.model_name"] == "claude-haiku-5-5"


def test_sdk_failure_marks_model_and_agent_spans_and_cleans_up(tmp_path):
    def handle(request):
        return httpx2.Response(500, json={"type": "error", "error": {"type": "api_error", "message": "Test failure"}})

    with Anthropic(api_key="test-placeholder", max_retries=0,
                   http_client=httpx2.Client(transport=httpx2.MockTransport(handle))) as client:
        with pytest.raises(InternalServerError):
            run_and_record(client, "Check ORD-001", "claude-haiku-5-5", str(tmp_path))
    assert not AnthropicInstrumentor().is_instrumented_by_opentelemetry
    spans = [json.loads(line) for line in next(tmp_path.glob("*.otel.jsonl")).read_text().splitlines()]
    for kind in ("AGENT", "LLM"):
        span = next(s for s in spans if s["attributes"].get("openinference.span.kind") == kind)
        assert span["status"]["status_code"] == "ERROR"
