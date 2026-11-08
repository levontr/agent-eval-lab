# Agent Eval Lab

A small Claude agent for a fictional store, with tests for what it does and what
it claims to have done.

The agent can look up an order, read a refund policy, and issue a simulated
refund. The interesting part is the evaluation: a prompt change made it refund
an order when the customer only asked about eligibility. The test suite caught it.

| Experiment | Scenarios passed |
| --- | --- |
| Original prompt | 3/3 |
| Prompt changed to refund proactively | 2/3 |
| Original prompt restored | 3/3 |

These are individual runs on three cases, not a reliability benchmark.
[Experiment details](docs/results.md).

## Try it

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).
Run commands from the repository root.

```bash
uv sync --locked
uv run pytest -q
```

The 55 tests run without an API key. They cover store rules, the agent loop,
tracing, evaluation checks, and judge response handling. SDK integration tests
use fake HTTP responses.

For live runs, export `ANTHROPIC_API_KEY` in your terminal. A `.env` file is not
loaded automatically. These commands use API credits:

```bash
# Ask the agent
uv run python -m support_agent_lab.agent "Is ORD-001 eligible for a refund?"

# Run and evaluate all three scenarios
uv run python -m support_agent_lab.runner

# Check the separate answer judge against four labeled examples
uv run python -m support_agent_lab.check_judge
```

The default model is `claude-haiku-5-5`. Each live command accepts
`--model MODEL_ID` if you want to use another available Claude model.
The judge is separate from the agent runner; running the suite does not call it.

## How it works

```text
Scenario → agent → Claude API ↔ local store tools
               ↓
        recorded execution → Python checks → report

Saved answer + tool evidence → separate LLM judge → supported / unsupported
```

- The agent loop is plain Python using the Anthropic SDK.
- OpenInference automatically instruments model calls. Agent and tool spans are explicit.
- The scenario runner resets the store before each case and continues after failures.
- The answer judge checks refund claims against tool evidence. Its expected labels
  are never included in the judging request.

## Read the code

| File | Purpose |
| --- | --- |
| [agent.py](src/support_agent_lab/agent.py) | Prompt, tool definitions, and bounded agent loop |
| [store.py](src/support_agent_lab/store.py) | Fake orders and refund rules |
| [telemetry.py](src/support_agent_lab/telemetry.py) | OpenTelemetry and OpenInference setup |
| [runner.py](src/support_agent_lab/runner.py) | Scenario execution and reports |
| [evaluate.py](src/support_agent_lab/evaluate.py) | Deterministic checks of tool behavior |
| [judge.py](src/support_agent_lab/judge.py) | One answer-grounding judgment |

[Scenarios](evals/README.md) · [Judge examples](examples/evaluation/README.md) ·
[Evaluation notes](docs/evaluation-guide.md) · [Build history](docs/build-journal.md)

## Output

A suite run writes `runs/experiment-<id>/report.json` and two files per case:

- `case-001.json`: our summary, used by the evaluator.
- `case-001.otel.jsonl`: OpenTelemetry spans, one JSON object per line.

Judge checks write `runs/judge-check-<id>.json`. Reports and traces are ignored by
Git. They can contain prompts, tool data, and API error details; review them before
sharing. Traces stay local—there is no hosted collector or dashboard.

## Limits

This is a learning project, not a payment service. All refunds are simulated and
store state lives in memory. Tools enforce eligibility and duplicate protection;
customer authorization is currently a prompt instruction, not a hard execution gate.

There are three agent scenarios and four judge examples. The judge matched all
four in the recorded batch, but those examples were used during development and
are not a held-out test set. Recorded tool results are trusted evidence.
The CLI runs sequentially; its tracing setup does not support concurrent runs.

Built with AI assistance, then inspected and tested through the experiments above.
Inspired by [Evaluating AI agents: moving past the vibe check](https://developers.googleblog.com/evaluating-ai-agents-moving-past-the-vibe-check/).
