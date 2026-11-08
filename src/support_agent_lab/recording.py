"""Save observable agent execution for later evaluation."""

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from support_agent_lab.agent import SYSTEM_PROMPT, TOOLS, run_agent
from support_agent_lab.telemetry import Attr, trace_run


def run_and_record(client, prompt: str, model: str, runs_dir: str, *, run_id: str | None = None) -> str:
    directory = Path(runs_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{run_id or uuid4().hex}.json"
    trace = {
        "schema_version": 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "model": model,
        "system_prompt": SYSTEM_PROMPT,
        "tools": TOOLS,
        "model_requests": 0,
        "model_responses": [],
        "tool_calls": [],
        "status": "running",
        "final_answer": None,
        "error_type": None,
    }
    started = perf_counter()
    try:
        with trace_run(path.with_suffix(".otel.jsonl"), prompt) as span:
            trace["otel_trace_id"] = format(span.get_span_context().trace_id, "032x")
            answer = run_agent(client, prompt, model, trace=trace)
            span.set_attribute(Attr.OUTPUT_VALUE, answer)
        trace["final_answer"] = answer
        trace["status"] = "completed"
        return answer
    except Exception as error:
        trace["status"] = "failed"
        # Avoid storing arbitrary exception text, which may contain credentials.
        trace["error_type"] = type(error).__name__
        raise
    finally:
        trace["duration_seconds"] = perf_counter() - started
        trace["token_usage"] = {
            key: sum(response["usage"].get(key, 0) or 0 for response in trace["model_responses"])
            for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        }
        path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
        print(f"[run] Saved {path}")
