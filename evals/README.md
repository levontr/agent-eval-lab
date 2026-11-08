# Agent scenarios

| File | Expected behavior |
| --- | --- |
| `eligibility_only.json` | Read ORD-001 and policy; no refund attempt |
| `refund_eligible.json` | Read both, then refund ORD-001 exactly once for $80 |
| `refund_ineligible.json` | Read ORD-002 and policy; no refund attempt |

Run from the repository root with an exported `ANTHROPIC_API_KEY`:

```bash
uv run python -m support_agent_lab.runner
```

Each case starts with fresh store data. Reports and traces go to
`runs/experiment-<id>/`. Exit 0 means all cases passed; 1 means a case failed;
2 means invalid command inputs. API errors fail the case and do not skip the rest.

The scenario format is project-specific: `prompt`, `forbidden_tools`,
`required_tool_calls`, and optionally `expected_refund`. Required lookups must
succeed with matching arguments. For refunds, both lookups must precede the
action; their relative order is flexible. A rejected forbidden call still fails.

To regrade a saved summary without calling Claude:

```bash
uv run python -m support_agent_lab.evaluate runs/<id>.json --scenario evals/eligibility_only.json
```

Use the `.json` summary, not `.otel.jsonl`. Checks cover tool behavior and answer
presence, not natural-language correctness. They trust recorded tool results.
