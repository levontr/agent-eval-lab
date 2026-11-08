# Project checkpoints

This log summarizes the project at each checkpoint. The [build journal](docs/build-journal.md)
contains the detailed commands and explanations. These are learning milestones,
not published package releases; the package version remains `0.1.0`.

## 2026-11-08 — Standalone refund-outcome judge

- Added a narrow rubric, output schema, and single-run judging command.
- Added four synthetic examples with separately stored reviewed labels.
- Added a batch judge check with saved reports and separate match, disagreement,
  and error counts; expected labels are never sent to the model.
- 55 offline tests pass. The user's live batch matched all four labels with no
  errors. This is a small sanity check, not a general reliability estimate.
- Judge commands remain separate from the agent runner. No `--judge` integration
  was added, as requested by the user.

## 2026-11-08 — Sequential evaluation runner

- One command runs every scenario, records it, grades it, and writes a report.
- Resets fixture data before each case and restores caller state after the suite.
- Continues after case failures, preserving failed-run evidence and error types.
- Saves scenario/fixture snapshots and per-case results in an experiment directory.
- 40 offline tests pass, including complete real-SDK flows over fake HTTP and a
  failed case that changes state before the next scenario starts.
- Inspected the user's live experiment: all three scenarios passed all configured checks.

## 2026-11-08 — Three scenario expectations

- Added eligible-refund and ineligible-refund scenarios.
- Strengthened eligibility inquiry with required order/policy lookups.
- Added checks for exactly one successful refund of the right order and amount,
  with supporting lookups before the action.
- 36 offline tests pass. The saved live eligibility run passes the stronger checks.
- Runner and live executions of the expanded suite remain the next checkpoint.

## 2026-11-08 — First behavioral evaluation (`1438323`)

- Added an explicit eligibility-only scenario and a CLI to evaluate saved summaries.
- Checks completion, answer presence, and absence of refund calls, including
  rejected attempts. Rejects mismatched questions and missing tool records.
- The user's saved eligibility run passed; no new model calls were made.
- 28 tests pass, including intentional evaluator failure cases.
- This is one behavioral rule, not a general accuracy or reliability score.
- Added an evaluation reference guide distinguishing general practices from project scope.

## 2026-11-08 — Automatic Anthropic instrumentation (`b9905fd`)

- Replaced `call_model()` with direct SDK calls and `AnthropicInstrumentor`.
- Kept explicit agent and tool spans and both local output formats.
- Instrumentation is enabled and removed for each sequential CLI run. Existing
  process-wide instrumentation is rejected rather than overwritten.
- 22 tests pass, including real SDK calls over a fake HTTP transport: one LLM
  span per request, token counts, parent links, sequential runs, and API failures.
- Inspected the user's live run: three automatic LLM spans, two explicit TOOL
  spans, one AGENT span, correct parent links, and no duplicate model spans.
- Automatic spans may include request/response content and API exception details.
- Next: implement the first behavioral evaluation.

## 2026-11-08 — Manual OpenTelemetry tracing (`c0bdaf0`)

### Current capabilities

- Python package managed by uv, with locked dependencies and pytest tests.
- Claude support agent with a manually implemented, bounded tool-calling loop.
- Three tools: order lookup, refund policy, and simulated refunds.
- Tool-level enforcement of refund eligibility and duplicate protection.
- Custom JSON run summaries with outcomes, usage, timing, and partial failures.
- OpenTelemetry spans for the agent, model requests, and local tool executions.
- OpenInference attribute conventions identifying `AGENT`, `LLM`, and `TOOL` spans.
- Local `.otel.jsonl` export linked to the custom summary by trace ID.

### Design at this checkpoint

`telemetry.py` explicitly instruments model calls through `call_model()`.
OpenInference's automatic Anthropic instrumentation is not enabled. The provider
and exporter are scoped to each CLI run. No remote trace service is configured.
The custom summary and standard span representation intentionally coexist for
comparison while learning.

### Validation and limitations

- 20 offline tests cover store behavior, the agent protocol, recording, span
  relationships, and failure status.
- User-provided live outputs verified eligibility inquiries and an explicit refund.
- A real custom JSON summary was inspected; no live OpenTelemetry artifact has
  yet been inspected by the assistant.
- Store state resets with each process; refunds never move real money.
- Customer intent is enforced by model instructions, not a deterministic
  authorization gate. Behavioral evaluations are still to be implemented.
- No trace viewer, automated evaluation suite, CI, or GitHub publication yet.

### Next checkpoint

Replace the manual model-call tracing wrapper with OpenInference's Anthropic
auto-instrumentation. Keep explicit agent/tool spans and verify there are no
duplicate model spans. This migration has not started.

## Earlier committed checkpoints

| Commit | Checkpoint |
| --- | --- |
| `e89114f` | Custom JSON run recording with tool results and token usage |
| `6d57940` | Claude support agent, simulated refunds, and tool tests |
| `136f28a` | uv package foundation and initial order lookup tool |
