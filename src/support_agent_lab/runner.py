"""Run a small scenario suite sequentially, saving evidence and a report."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4

from anthropic import Anthropic

from support_agent_lab import store
from support_agent_lab.evaluate import evaluate_run
from support_agent_lab.recording import run_and_record


def load_scenarios(directory: Path) -> list[dict]:
    scenarios = []
    for path in sorted(directory.glob("*.json")):
        scenario = json.loads(path.read_text())
        if not isinstance(scenario, dict) or not all(
            isinstance(scenario.get(key), str) and scenario[key].strip()
            for key in ("id", "prompt")
        ):
            raise ValueError(f"Invalid scenario ID or prompt: {path}")
        if not isinstance(scenario.get("forbidden_tools"), list) or not all(
            isinstance(name, str) for name in scenario["forbidden_tools"]
        ):
            raise ValueError(f"Invalid forbidden_tools: {path}")
        required = scenario.get("required_tool_calls", [])
        if not isinstance(required, list) or any(
            not isinstance(call, dict) or not isinstance(call.get("name"), str)
            or not isinstance(call.get("arguments"), dict) for call in required
        ):
            raise ValueError(f"Invalid required_tool_calls: {path}")
        if "expected_refund" in scenario:
            expected = scenario["expected_refund"]
            if not isinstance(expected, dict) or not isinstance(expected.get("order_id"), str) or type(expected.get("amount_usd")) not in (int, float):
                raise ValueError(f"Invalid expected_refund: {path}")
        # Exercise expectations before spending API credits on any scenario.
        evaluate_run({"schema_version": 1, "prompt": scenario["prompt"],
                      "tool_calls": [], "status": "failed", "final_answer": None}, scenario)
        scenarios.append(scenario)
    if not scenarios:
        raise ValueError(f"No scenario JSON files found in {directory}")
    if len({s["id"] for s in scenarios}) != len(scenarios):
        raise ValueError("Scenario IDs must be unique")
    return scenarios


def run_suite(client, scenarios: list[dict], model: str, output_dir: Path) -> dict:
    """Execute fresh runs; preserve the caller's store even when a case fails."""
    if not scenarios:
        raise ValueError("Cannot run an empty scenario suite")
    experiment_dir = output_dir / f"experiment-{uuid4().hex}"
    experiment_dir.mkdir(parents=True)
    report = {
        "schema_version": 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "scenarios": scenarios,
        "initial_orders": deepcopy(store.INITIAL_ORDERS),
        "results": [],
    }
    original_orders = store.ORDERS
    try:
        for index, scenario in enumerate(scenarios, start=1):
            store.reset_store()
            run_id = f"case-{index:03d}"
            run_path = experiment_dir / f"{run_id}.json"
            error_type = None
            try:
                run_and_record(client, scenario["prompt"], model, str(experiment_dir), run_id=run_id)
            except Exception as error:
                error_type = type(error).__name__

            try:
                result = evaluate_run(json.loads(run_path.read_text()), scenario)
            except (OSError, ValueError, KeyError, TypeError) as error:
                result = {"scenario_id": scenario["id"], "passed": False, "checks": {},
                          "evaluation_error_type": type(error).__name__}
            if error_type:
                result["passed"] = False
                result["execution_error_type"] = error_type
            result["run_file"] = run_path.name if run_path.exists() else None
            report["results"].append(result)
            report["passed_count"] = sum(row["passed"] for row in report["results"])
            report["total"] = len(scenarios)
            report["passed"] = len(report["results"]) == len(scenarios) and report["passed_count"] == len(scenarios)
            (experiment_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            label = "PASS" if result["passed"] else "FAIL"
            print(f"[{label}] {scenario['id']}")
            for check, passed in result["checks"].items():
                if not passed:
                    print(f"  Failed check: {check}")
            if error_type:
                print(f"  Execution error: {error_type}")
    finally:
        store.ORDERS = original_orders

    print(f"\n{report['passed_count']}/{report['total']} scenarios passed")
    print(f"[report] Saved {experiment_dir / 'report.json'}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run and evaluate scenarios (uses Claude API credits).")
    parser.add_argument("--scenarios-dir", type=Path, default=Path("evals"))
    parser.add_argument("--output-dir", type=Path, default=Path("runs"))
    parser.add_argument("--model", default="claude-haiku-5-5")
    args = parser.parse_args()
    try:
        scenarios = load_scenarios(args.scenarios_dir)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    if not os.environ.get("ANTHROPIC_API_KEY"):
        parser.error("Export ANTHROPIC_API_KEY in this terminal first.")
    with Anthropic(timeout=30.0, max_retries=0) as client:
        report = run_suite(client, scenarios, args.model, args.output_dir)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
