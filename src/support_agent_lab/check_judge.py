"""Compare judge decisions with reviewed labels on a small fixture set."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4

from anthropic import Anthropic

from support_agent_lab.judge import build_evidence, judge_run


def load_examples(labels_path: Path) -> list[dict]:
    labels = json.loads(labels_path.read_text())
    if not isinstance(labels, list) or not labels:
        raise ValueError("Labels must be a nonempty list.")
    examples = []
    seen = set()
    for label in labels:
        if (
            not isinstance(label, dict) or not isinstance(label.get("file"), str)
            or type(label.get("expected_supported")) is not bool
        ):
            raise ValueError("Each label requires file (string) and expected_supported (boolean).")
        if label["file"] in seen:
            raise ValueError("Duplicate example file in labels.")
        seen.add(label["file"])
        run = json.loads((labels_path.parent / label["file"]).read_text())
        build_evidence(run)  # Validate all examples before spending API credits.
        examples.append({**label, "run": run})
    return examples


def check_judge(client, examples: list[dict], model: str, rubric: str, schema: dict, output_dir: Path) -> dict:
    if not examples:
        raise ValueError("Cannot check a judge without examples.")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"judge-check-{uuid4().hex}.json"
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "model": model, "rubric": rubric, "schema": schema,
        "examples": examples, "results": [], "total": len(examples),
    }
    for example in examples:
        row = {"file": example["file"], "expected_supported": example["expected_supported"]}
        try:
            # Only the run is sent to judge_run, never the expected label.
            judgment = judge_run(client, example["run"], model, rubric, schema)
            row["judgment"] = judgment
            row["status"] = "match" if judgment["supported"] == example["expected_supported"] else "disagreement"
        except Exception as error:
            row["status"] = "error"
            row["error_type"] = type(error).__name__
        report["results"].append(row)
        for status in ("match", "disagreement", "error"):
            report[f"{status}_count"] = sum(result["status"] == status for result in report["results"])
        report["completed"] = len(report["results"]) == len(examples)
        report["passed"] = report["match_count"] == len(examples)
        path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"[{row['status'].upper()}] {example['file']}")
        if "judgment" in row:
            print(f"  {row['judgment']['reason']}")
        else:
            print(f"  Error: {row['error_type']}")
    print(f"\n{report['match_count']}/{report['total']} matched; "
          f"{report['disagreement_count']} disagreements; {report['error_count']} errors")
    print(f"[report] Saved {path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the refund judge against reviewed examples (uses API credits).")
    parser.add_argument("--labels", type=Path, default=Path("examples/evaluation/labels.json"))
    parser.add_argument("--rubric-dir", type=Path, default=Path("evals/judges"))
    parser.add_argument("--model", default="claude-haiku-5-5")
    parser.add_argument("--output-dir", type=Path, default=Path("runs"))
    args = parser.parse_args()
    try:
        examples = load_examples(args.labels)
        rubric = (args.rubric_dir / "refund_outcome.prompt.txt").read_text()
        schema = json.loads((args.rubric_dir / "refund_outcome.schema.json").read_text())
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if not os.environ.get("ANTHROPIC_API_KEY"):
        parser.error("Export ANTHROPIC_API_KEY in this terminal first.")
    with Anthropic(timeout=30.0, max_retries=0) as client:
        report = check_judge(client, examples, args.model, rubric, schema, args.output_dir)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
