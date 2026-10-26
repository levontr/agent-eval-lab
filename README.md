# Support Agent Lab

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

These are local JSON records, not yet OpenTelemetry traces or evaluation scores.
Usage totals cover received responses; a failed API request may have unknown
usage. No dollar cost is calculated. `runs/` is ignored by Git because records
contain user input and tool data. No API key is recorded explicitly.

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
