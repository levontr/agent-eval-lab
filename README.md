# Support Agent Lab

For the concepts behind the project, see the [evaluation guide](docs/evaluation-guide.md).

A small learning project: build a customer-support agent, then evaluate its
answers and tool use against repeatable scenarios.

The intended agent will look up orders, consult a refund policy, and issue
simulated refunds. Evaluation will check both customer outcomes and the tool
calls used to produce them. All store data is fictional.

**Status:** store tools and a Claude agent with lookup, policy, and simulated
refunds are implemented. Live order lookup was verified by the user. The full
refund workflow is tested offline; live refund behavior and evaluations are next.

See the [build journal](docs/build-journal.md) for completed steps and commands,
and the [roadmap](docs/roadmap.md) for upcoming checkpoints.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
uv sync --locked
```

## Current checkpoint: the fake store

`src/support_agent_lab/store.py` contains three fake orders and the `get_order` tool. There is no LLM
connected yet. Try a lookup:

```bash
uv run support-agent ORD-001
uv run support-agent ORD-999
uv run support-agent --help
```

## Project files

- `src/support_agent_lab/store.py`: fake data, order lookup, and simulated refunds.
- `src/support_agent_lab/cli.py`: command-line argument handling and output.
- `src/support_agent_lab/policy.py`: fictional refund rules exposed as a tool.
- `src/support_agent_lab/__init__.py`: identifies the Python package.
- `pyproject.toml`: project metadata, Python requirement, and dependencies.
- `.python-version`: Python version selected by uv.
- `uv.lock`: dependency resolution managed by uv; commit this file.
- `.venv/`: local environment managed by uv; do not commit this folder.

The `anthropic` SDK connects to Claude; `uv_build` builds the package.
When we need a runtime dependency, use `uv add` to
update the project and lockfile together. Use `uv run` to run commands inside
the project environment without manually activating it.

## First model call

In a terminal where `ANTHROPIC_API_KEY` is exported, run:

```bash
uv run python -m support_agent_lab.llm "Say hello in one sentence."
```

This sends one API request and uses API credits. It does not yet use our store
tools. The default model is `claude-haiku-5-5`; override with `--model MODEL_ID`
if needed. The SDK reads the key from the environment; never commit the key.
This command does not automatically load `.env` files.

## Support agent

```bash
uv run python -m support_agent_lab.agent "What happened to order ORD-001?"
```

Requires `ANTHROPIC_API_KEY` in the environment and uses API credits. Prints each
tool call and its result, then the final answer. Claude has order lookup, policy,
and simulated refund tools. The loop stops after at most five model requests.

Compare an eligibility question with a refund request:

```bash
uv run python -m support_agent_lab.agent "Is ORD-001 eligible for a refund?"
uv run python -m support_agent_lab.agent "Please refund ORD-001 if eligible."
```

The first should only look up the order and policy. The second should additionally
call `issue_refund`. Each command starts with fresh store data. Customer intent
and checking the policy first are prompt instructions, not hard enforcement in
the dispatcher; upcoming evaluations will measure whether Claude follows them.

## Run records

Each agent CLI invocation saves `runs/<unique-id>.json` and prints its path.
Use `--runs-dir DIRECTORY` to choose another location. Records include the
request, requested/returned model IDs, prompt and tool definitions, ordered tool
calls and results, final answer, elapsed time, and API-reported token usage.
Failed runs save partial progress and an error type, then raise the error.

The summary JSON is our custom format, not an evaluation score.
Usage totals cover received responses; a failed API request may have unknown
usage. No dollar cost is calculated. `runs/` is ignored by Git because records
contain user input and tool data. No API key is recorded explicitly.

Each run also writes `runs/<same-id>.otel.jsonl`: one OpenTelemetry span per
line, using OpenInference's `AGENT`, `LLM`, and `TOOL` labels. Model requests and
tool executions are children of the agent span. The summary's `otel_trace_id`
links to this trace. Spans include timing, tool inputs/results, model input/output
token counts, and failure status. The summary retains fuller API usage details.

Model requests are automatically instrumented by `AnthropicInstrumentor` using
our OpenTelemetry provider. Agent and local tool spans remain explicit in our
code. The SDK's console exporter writes to a
local file; this is not OTLP wire format. A collector/dashboard and the article's
evaluation toolkit are not connected yet. No telemetry is sent to a remote service.

The instrumentor wraps SDK methods process-wide. This CLI enables it for one run
and removes it afterward; concurrent or nested recorded runs are not supported.
Auto-instrumentation can capture message content and API exception details, unlike
our earlier model wrapper. Local trace files should be reviewed before sharing.

## First behavioral evaluation

Evaluate an existing summary (replace the run ID with yours):

```bash
uv run python -m support_agent_lab.evaluate runs/<id>.json --scenario evals/eligibility_only.json
```

The scenario declares an exact eligibility-only question and forbids
`issue_refund`. Checks require completion, a nonempty answer, and absence of that
tool call. Even a rejected refund attempt fails. Exit codes: 0 for pass, 1 for
failed checks, 2 for invalid input or a mismatched scenario. No model call is
made. Use the custom `.json` summary, not `.otel.jsonl`.

The [three-scenario dataset](evals/README.md) also checks required lookups and,
for eligible refund requests, one successful refund of the correct order/amount
after those lookups.

Run all three scenarios and evaluate them automatically:

```bash
uv run python -m support_agent_lab.runner
```

Run from the project root with `ANTHROPIC_API_KEY` exported. This uses API credits,
resets the store before each case, and saves a combined report under
`runs/experiment-<id>/report.json` with each case's traces beside it. It prints
PASS/FAIL per case and a total; no copying run IDs is needed. A case failure does
not skip the remaining cases. Exit code 1 means at least one case failed.

These checks do not grade natural-language answer accuracy or latency.
A run can pass it while failing future evaluations. No external evaluation
toolkit is connected yet.

## Tests

```bash
uv run pytest -q
```

The tests verify lookups, full refunds, rejected refunds without state changes,
duplicate protection, and the two-day eligibility boundary. Each test gets an
isolated copy of the store. No API key or LLM is needed.

## Learning path

Refunds only change in-memory data within the current Python process. Restarting
Python resets the store. No real payments or persistent storage are involved.

1. Fake store and order lookup (current checkpoint).
2. Refund policy and simulated refund tool.
3. LLM agent that chooses and calls tools.
4. Capture execution traces and define evaluation scenarios.
5. Connect evaluation tooling and compare agent changes.
