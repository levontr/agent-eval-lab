# Support Agent Lab

A small learning project: build a customer-support agent, then evaluate its
answers and tool use against repeatable scenarios.

The intended agent will look up orders, consult a refund policy, and issue
simulated refunds. Evaluation will check both customer outcomes and the tool
calls used to produce them. All store data is fictional.

**Status:** project setup and order lookup are implemented. The agent and
evaluation pipeline are planned; no model or evaluation results exist yet.

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

- `src/support_agent_lab/store.py`: fake data and the first tool.
- `src/support_agent_lab/cli.py`: command-line argument handling and output.
- `src/support_agent_lab/__init__.py`: identifies the Python package.
- `pyproject.toml`: project metadata, Python requirement, and dependencies.
- `.python-version`: Python version selected by uv.
- `uv.lock`: dependency resolution managed by uv; commit this file.
- `.venv/`: local environment managed by uv; do not commit this folder.

There are no third-party runtime dependencies yet; `uv_build` builds the package.
When we need a runtime dependency, use `uv add` to
update the project and lockfile together. Use `uv run` to run commands inside
the project environment without manually activating it.

## Learning path

1. Fake store and order lookup (current checkpoint).
2. Refund policy and simulated refund tool.
3. LLM agent that chooses and calls tools.
4. Capture execution traces and define evaluation scenarios.
5. Connect evaluation tooling and compare agent changes.
