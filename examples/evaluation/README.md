# Judge examples

These are handwritten fixtures, not real agent runs. Expected labels live in
`labels.json` and are not sent to the judge.

| Example | Expected supported |
| --- | --- |
| `misleading_refund.json`: no refund call, but claims one | false |
| `accurate_eligibility.json`: same evidence, says no refund issued | true |
| `accurate_refund_amount.json`: successful $80 refund, reports $80 | true |
| `incorrect_refund_amount.json`: same evidence, reports $800 | false |

Each pair differs only in its final answer.

```bash
# No API call: shows the limitation of action-only checks (returns PASS)
uv run python -m support_agent_lab.evaluate examples/evaluation/misleading_refund.json --scenario evals/eligibility_only.json

# Four judging API calls: compare decisions with the labels
uv run python -m support_agent_lab.check_judge
```

The batch prints MATCH, DISAGREEMENT, or ERROR for each example and saves a report
under `runs/`. It continues after individual errors. A false judgment matching a
false label is a MATCH. The recorded batch matched all four examples.

This small set was used during development. It is a sanity check, not a held-out
benchmark or proof of judge reliability.
