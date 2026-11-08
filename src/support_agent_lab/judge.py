"""Judge one completed run's refund claims; never execute the store tools."""

import argparse
import json
import os
from pathlib import Path

from anthropic import Anthropic


def build_evidence(run: dict) -> dict:
    """Select evidence only, excluding metadata and any expected judge label."""
    if not isinstance(run, dict) or run.get("schema_version") != 1:
        raise ValueError("Expected a version-1 run summary JSON object.")
    if run.get("status") != "completed":
        raise ValueError("Judge requires a completed run; partial traces are not sufficient evidence.")
    for field in ("prompt", "final_answer"):
        if not isinstance(run.get(field), str) or not run[field].strip():
            raise ValueError(f"Run requires a nonempty {field}.")
    calls = run.get("tool_calls")
    if not isinstance(calls, list) or any(
        not isinstance(call, dict) or not isinstance(call.get("name"), str)
        or not isinstance(call.get("arguments"), dict)
        or not isinstance(call.get("result"), dict)
        for call in calls
    ):
        raise ValueError("Run requires tool calls with name, arguments, and result.")
    return {
        "customer_request": run["prompt"],
        "tool_calls": [{key: call[key] for key in ("name", "arguments", "result")} for call in calls],
        "final_answer": run["final_answer"],
    }


def judge_run(client, run: dict, model: str, rubric: str, schema: dict) -> dict:
    evidence = build_evidence(run)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=rubric,
        messages=[{"role": "user", "content": json.dumps(evidence)}],
        output_config={"format": {"type": "json_schema", "schema": schema}},
    )
    if response.stop_reason != "end_turn":
        raise ValueError(f"Judge did not finish normally: {response.stop_reason}")
    text = "\n".join(block.text for block in response.content if block.type == "text")
    result = json.loads(text)
    # Validate locally too: malformed or incomplete judgments must never count as passes.
    if (
        not isinstance(result, dict) or set(result) != {"supported", "reason"}
        or type(result["supported"]) is not bool
        or not isinstance(result["reason"], str) or not result["reason"].strip()
    ):
        raise ValueError("Judge must return supported (boolean) and a nonempty reason (string).")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Judge a saved answer's refund claims (uses API credits).")
    parser.add_argument("run", type=Path, help="Completed run summary .json, not .otel.jsonl")
    parser.add_argument("--model", default="claude-haiku-5-5")
    parser.add_argument("--rubric-dir", type=Path, default=Path("evals/judges"))
    args = parser.parse_args()
    try:
        run = json.loads(args.run.read_text())
        build_evidence(run)
        rubric = (args.rubric_dir / "refund_outcome.prompt.txt").read_text()
        schema = json.loads((args.rubric_dir / "refund_outcome.schema.json").read_text())
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if not os.environ.get("ANTHROPIC_API_KEY"):
        parser.error("Export ANTHROPIC_API_KEY in this terminal first.")
    with Anthropic(timeout=30.0, max_retries=0) as client:
        try:
            result = judge_run(client, run, args.model, rubric, schema)
        except ValueError as error:
            parser.error(str(error))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["supported"] else 1)


if __name__ == "__main__":
    main()
