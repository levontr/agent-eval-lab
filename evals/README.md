# Three-scenario evaluation dataset

Each case assumes a fresh copy of the fictional store: ORD-001 is 3 days late
and not refunded; ORD-002 is on time. The runner resets store state
before every case. Run all three cases from the project root:

```bash
uv run python -m support_agent_lab.runner
```

This makes live Claude calls using `ANTHROPIC_API_KEY`. Cases execute sequentially,
and each receives fresh initial store data. Failures are recorded and remaining
cases continue. It creates `runs/experiment-<id>/report.json` plus each case's
`.json` summary and `.otel.jsonl` spans. The report includes scenario snapshots,
initial fixture data, individual checks, and totals. Exit code is 0 if all cases
pass, 1 if any fail, and 2 for CLI configuration/input errors.

Use `--model`, `--scenarios-dir`, or `--output-dir` to override defaults. This first
runner executes each scenario once; it is not a reliability estimate. No CI or
LLM judge is required. API/infra failures appear as failures, with error types
distinguishing them from behavioral check failures.

| Scenario | Expected tool behavior |
| --- | --- |
| `eligibility_only.json` | Read ORD-001 and policy; do not attempt a refund |
| `refund_eligible.json` | Read ORD-001 and policy, then refund ORD-001 exactly once for $80 |
| `refund_ineligible.json` | Read ORD-002 and policy; do not attempt a refund |

Fields in our custom scenario format:

- `id`: stable scenario identifier.
- `prompt`: exact customer input, also checked when grading a saved summary.
- `forbidden_tools`: any call to these tools fails, even if the tool rejects it.
- `required_tool_calls`: required names and arguments with non-error results.
- `expected_refund`: if present, requires exactly one refund attempt with matching
  arguments and a successful result for the specified order and amount. Required
  lookups must occur before it; the two lookups may happen in either order.

All cases require completed execution and a nonempty answer. These checks assess
tool behavior, not natural-language answer correctness. We trust recorded tool
results as execution evidence; initial/final store snapshots are not graded yet.

The original eligibility scenario was strengthened with required lookups at this
checkpoint. Compare future agent versions using this same dataset revision;
scores from older, weaker checks are not directly comparable.

Run one saved summary through its scenario:

```bash
uv run python -m support_agent_lab.evaluate runs/<id>.json --scenario evals/refund_eligible.json
```
