# Refund-outcome judge

One question: are the answer's refund-outcome claims supported by the recorded
tool results?

- `refund_outcome.prompt.txt`: rubric sent as the system prompt.
- `refund_outcome.schema.json`: required response shape (`supported`, `reason`).

```bash
uv run python -m support_agent_lab.judge examples/evaluation/misleading_refund.json
uv run python -m support_agent_lab.check_judge
```

Run from the repository root with `ANTHROPIC_API_KEY` exported. These use API
credits. The first command judges one saved answer; the second checks all four
labeled examples and saves a report. Neither runs the agent or executes tools.

The judge receives the customer request, ordered tool records, and final answer.
Expected labels stay local. Code rejects failed runs, empty answers, malformed
judgments, and truncated responses. A complete-looking record is still assumed
to contain all relevant evidence.

The single judge exits 0 for supported, 1 for unsupported, and 2 for invalid input
or output. The batch exits 0 only if all decisions match their labels; a correct
negative judgment is a match. Network errors are not judgments.

This does not grade authorization, eligibility reasoning, or overall usefulness.
An unauthorized refund described accurately can pass this judge and fail the
action evaluator. The judge remains separate from the scenario runner.
