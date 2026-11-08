# Evaluation notes

A scenario defines the input, initial state, and expected behavior. A runner
executes it. A trace records what happened. An evaluator checks that evidence.

## What to rerun

Changing the agent, model, or prompt requires new executions. Regrading an old
trace only tells you something about that old execution. Changing an evaluator
can justify regrading stored traces.

Keep scenarios and checks fixed when comparing versions. Reset mutable state
between cases. Repeat important cases: one pass is not a reliability estimate.
Record model, code, prompt, dataset, and evaluator versions for serious comparisons.
Our runner saves scenario snapshots, fixtures, and the requested model; it does
not yet capture every version automatically.

## Code checks and LLM judges

Use code for precise rules: tool names, arguments, counts, amounts, and order of
actions. Use a judge for questions requiring interpretation, such as whether an
answer accurately describes the result. Validate the judge against reviewed
examples and inspect disagreements. A valid JSON response can still be wrong.

Neither approach replaces authorization checks in execution code. A post-run
check can detect an unwanted refund, but cannot prevent it.

## Local, CI, and production

The same scenario suite can run locally or in CI. Offline evaluation means
controlled test data, not necessarily no network. This repository's CI uses fake
model responses; live evaluation is a separate command requiring an API key.

Production traces can be reviewed afterward or scored in background jobs. They
usually lack reference answers. Useful failures can become sanitized regression
cases. Keep real side effects out of test runs.

Commit scenarios, fixtures, evaluators, and code. Store routine reports and traces
as experiment artifacts. Review captured data before sharing it.

## Tracing in this project

OpenTelemetry supplies span IDs, timing, parent links, and export. OpenInference
supplies AI conventions and an Anthropic instrumentor. Model calls are automatic;
our agent and tool spans are explicit. The local `.otel.jsonl` files use the SDK's
diagnostic export format, not OTLP wire format. The evaluator currently reads our
separate summary JSON.

## References

- [OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/)
- [OpenInference](https://arize-ai.github.io/openinference/)
- [Evaluation lifecycle](https://docs.langchain.com/langsmith/evaluation)

LangSmith is a reference here, not a dependency. LangChain is not required.
