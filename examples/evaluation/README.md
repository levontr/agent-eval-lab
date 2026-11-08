# An answer our current checks miss

`misleading_refund.json` is a handwritten synthetic fixture, not a live run.
It records valid policy and order lookups, without a refund call. Its final
answer nevertheless claims a simulated refund was issued.

Run the existing tool-behavior evaluator:

```bash
uv run python -m support_agent_lab.evaluate examples/evaluation/misleading_refund.json --scenario evals/eligibility_only.json
```

Expected current result: **passed: true**. The checked actions are appropriate,
and an answer is present. No existing check assesses the answer's meaning.
This is a demonstration of limited evaluation coverage, not a successful answer.

The intended label for a future answer-grounding check is **false**: no refund
execution supports the answer's claim. That label is based on manual inspection
and should be reviewed by the learner before using it to assess a judge.

The judge complements the deterministic checks rather than replacing them. The optional
`python -m support_agent_lab.judge` command is now implemented; see
`evals/judges/README.md`. The deterministic demonstration above makes no API calls.

## Positive comparison

`accurate_eligibility.json` has identical evidence and metadata. Only the final
answer changes: it says the order is eligible and that no refund was issued.
Its expected judge label is **supported: true**. This contrast tests whether the
judge distinguishes a conditional refund from a claim of completed execution.

```bash
uv run python -m support_agent_lab.judge examples/evaluation/accurate_eligibility.json
```

The user ran the misleading example and received `supported: false` with a reason
correctly identifying the missing refund execution. The positive example returned
`supported: true`, correctly distinguishing eligibility from execution. Two
examples are a learning exercise, not judge calibration.

## Successful refund: correct versus incorrect amount

Two more handwritten examples record the same successful $80 simulated refund.
Only the final answer differs:

| File | Claimed amount | Expected supported |
| --- | --- | --- |
| `accurate_refund_amount.json` | $80 | true |
| `incorrect_refund_amount.json` | $800 | false |

```bash
uv run python -m support_agent_lab.judge examples/evaluation/accurate_refund_amount.json
uv run python -m support_agent_lab.judge examples/evaluation/incorrect_refund_amount.json
```

Each command makes one judging API call. The user reported both judgments matched
expectations. These are
synthetic records, not newly executed refunds. The earlier lookup says
`refunded=false`; the later successful refund changes that state. The judge must
read the sequence and result amount, rather than just notice a refund tool name.

## Check all four examples together

```bash
uv run python -m support_agent_lab.check_judge
```

`labels.json` stores the reviewed expected booleans separately from the evidence.
The command makes one judge request per example, compares the decision locally,
and reports MATCH, DISAGREEMENT, or ERROR. Labels are never sent to the model.
An expected false matched by a false judgment is a MATCH, not a failed test.

The report is saved as `runs/judge-check-<id>.json` with examples, labels, rubric,
schema, model, judgments/reasons, and separate counts. It saves progress after
each example and continues after individual errors. Exit code 0 means all match;
1 means at least one disagreement/error; 2 means invalid CLI inputs or setup.

This is a four-example sanity-check set already used while developing the judge,
not an independent held-out benchmark. Matching all four is not a reliability
claim. Additional cases and repeated judgments would be needed for calibration.
