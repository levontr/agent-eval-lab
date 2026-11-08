# Refund-outcome judge: specification checkpoint

This judge asks one question: **Are the final answer's refund-outcome claims
supported by the recorded tool results?**

- `refund_outcome.prompt.txt`: rubric that will be sent to the judging model.
- `refund_outcome.schema.json`: required shape of the judge's response.

The judging input will contain the customer request, ordered tool calls with
arguments/results, and final answer. The judge will not receive our expected
label; that is held separately to assess its decision.

For `examples/evaluation/misleading_refund.json`, the intended response is:

```json
{
  "supported": false,
  "reason": "The answer claims a simulated $80 refund was issued, but the record contains only policy and order lookups and no successful issue_refund result."
}
```

That is a manually written example of the expected judgment, not a model result.
Exact reason wording is not required. We will compare the boolean with reviewed
labels and inspect explanations for mistakes.

This judge cannot replace authorization checks: an unwanted refund might be
described accurately and pass this rubric while failing our tool-behavior check.
Likewise, an answer with no refund-outcome claim can pass this narrow rubric
without answering the customer's question well.

The input assumes a complete run record. Do not judge a partial trace as if it
proves that an omitted action never happened. Application code should gate the
judge on completed runs and validate its response; malformed output is an error,
not a pass. A schema specifies structure, not judgment quality.

## Run one judgment

From the project root with `ANTHROPIC_API_KEY` exported:

```bash
uv run python -m support_agent_lab.judge examples/evaluation/misleading_refund.json
```

This makes one Claude Messages API call with the rubric as the system prompt,
selected evidence as the user message, and the schema as `output_config.format`.
The judge has no store tools. It does not rerun the agent or issue refunds.
Override the default model with `--model MODEL_ID`.

`judge.py` checks evidence before the request and validates the reply locally.
Only completed summaries with an answer and valid tool records are accepted;
the caller must still ensure the record is complete. Truncation or malformed
output is an error, never a pass. Exit 0 means supported, 1 means unsupported,
and 2 means invalid input or judgment. SDK/network failures raise an exception.

This first command prints its judgment; it does not yet save a judge report or
integrate with the suite runner. Offline tests verify request construction and
failure handling, not whether the model's judgments agree with reviewed labels.
Next: inspect the live judgment, then test more positive and negative examples.

To compare all four reviewed examples at once, use
`uv run python -m support_agent_lab.check_judge`. This checks the judge itself;
`support_agent_lab.runner` still checks agent tool behavior and does not invoke
the judge. See `examples/evaluation/README.md` for labels and report details.
