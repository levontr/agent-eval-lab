"""Deterministic checks of recorded tool behavior against scenario expectations."""

import argparse
import json
from pathlib import Path


def evaluate_run(run: dict, scenario: dict) -> dict:
    """Check the saved summary against explicit expectations, not inferred intent."""
    if run.get("schema_version") != 1:
        raise ValueError("Expected a version-1 run summary (.json), not an OpenTelemetry span file.")
    if run.get("prompt") != scenario["prompt"]:
        raise ValueError("Run prompt does not match this evaluation scenario.")
    calls = run.get("tool_calls")
    if not isinstance(calls, list) or any(
        not isinstance(call, dict) or not isinstance(call.get("name"), str)
        for call in calls
    ):
        raise ValueError("Run summary is missing valid tool-call records.")

    forbidden_calls = [call["name"] for call in calls if call["name"] in scenario["forbidden_tools"]]
    checks = {
        "run_completed": run.get("status") == "completed",
        "final_answer_present": isinstance(run.get("final_answer"), str) and bool(run["final_answer"].strip()),
        "no_forbidden_tool_calls": not forbidden_calls,
    }

    # Match tool arguments, not just names. A lookup of the wrong order is not evidence.
    required = scenario.get("required_tool_calls", [])

    def matches(call, expected):
        return (
            call["name"] == expected["name"]
            and call.get("arguments") == expected["arguments"]
            and isinstance(call.get("result"), dict)
            and "error" not in call["result"]
        )

    if required:
        checks["required_lookups_succeeded"] = all(
            any(matches(call, expected) for call in calls) for expected in required
        )

    if "expected_refund" in scenario:
        expected = scenario["expected_refund"]
        refunds = [(index, call) for index, call in enumerate(calls) if call["name"] == "issue_refund"]
        checks["exactly_one_refund_attempt"] = len(refunds) == 1
        checks["correct_refund_succeeded"] = False
        checks["evidence_before_refund"] = False
        if len(refunds) == 1:
            index, call = refunds[0]
            result = call.get("result", {})
            checks["correct_refund_succeeded"] = (
                call.get("arguments") == {"order_id": expected["order_id"]}
                and isinstance(result, dict)
                and "error" not in result
                and result.get("status") == "refunded"
                and result.get("order_id") == expected["order_id"]
                and result.get("amount_usd") == expected["amount_usd"]
            )
            checks["evidence_before_refund"] = all(
                any(matches(earlier, lookup) for earlier in calls[:index])
                for lookup in required
            )
    return {
        "scenario_id": scenario["id"],
        "passed": all(checks.values()),
        "checks": checks,
        "observed_tools": [call["name"] for call in calls],
        "forbidden_calls": forbidden_calls,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a saved run without calling an LLM.")
    parser.add_argument("run", type=Path, help="Run summary .json file (not .otel.jsonl)")
    parser.add_argument("--scenario", type=Path, required=True)
    args = parser.parse_args()
    try:
        run = json.loads(args.run.read_text())
        scenario = json.loads(args.scenario.read_text())
        if not isinstance(run, dict) or not isinstance(scenario, dict):
            raise ValueError("Run and scenario must be JSON objects.")
        report = evaluate_run(run, scenario)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
