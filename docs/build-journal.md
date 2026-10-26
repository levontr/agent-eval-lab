# Build journal

This journal records what we actually implemented, why, and how to check it.
Future checkpoints will add their commands, decisions, and observed results.

## 01 — Fake store

Created `store.py` with three fictional orders and `get_order(order_id)`.
The function returns order facts or an explicit missing-order error. It will
eventually be exposed as a tool to the LLM.

Verified a known order and an unknown order by running the file directly.

## 02 — Reproducible Python setup

Chose uv to manage Python environments and dependencies.

Created these files manually (we did not run `uv init`):

- `pyproject.toml`: name, version, description, README, Python >=3.12, and an
  empty dependency list.
- `.python-version`: selects Python 3.12.
- `.gitignore`: excludes generated environments, caches, and `.env` secrets.
- `README.md`: setup and current usage.

Then ran:

```bash
uv sync --cache-dir .uv-cache
uv run --cache-dir .uv-cache python store.py ORD-001
```

The local cache flag was used because the coding workspace restricts writes
outside the project. It is not a requirement of the application.

`uv sync` generated `.venv/`, `.uv-cache/`, and `uv.lock`. uv selected an
available Python 3.12.8 interpreter. The lookup returned the expected order.

### Reproduce the current project after downloading or cloning it

Install uv, open a terminal in the project directory, and run:

```bash
uv sync --locked
uv run support-agent ORD-001
uv run support-agent ORD-999
```

The first lookup returns order details; the second returns `Order not found`.
No API key is needed at this checkpoint.

Commit source files, documentation, `.python-version`, `pyproject.toml`, and
`uv.lock`. Do not commit `.venv/`, caches, or API keys.

## 03 — Portfolio plan

Added a roadmap and this journal. The repository is not yet initialized with
Git or published to GitHub. Future milestones should use focused commits so
the code history complements the explanations here.

## 04 — Python package and command

Moved the store into `src/support_agent_lab/store.py` and added `__init__.py`
to identify the package. Moved terminal interaction into `cli.py`, using
Python's built-in `argparse` for the required order ID and help text.

Added two sections to `pyproject.toml`:

- `[build-system]` selects `uv_build` to build/install our package.
- `[project.scripts]` maps `support-agent` to `support_agent_lab.cli:main`.

Ran the following successfully:

```bash
uv sync --cache-dir .uv-cache
uv run --cache-dir .uv-cache --locked support-agent ORD-001
uv run --cache-dir .uv-cache --locked support-agent ORD-999
uv run --cache-dir .uv-cache --locked support-agent --help
```

uv installed the local package into `.venv` and updated `uv.lock`. Verified the
known order, missing-order error, and help output. Store behavior is unchanged.

Attempted `git init -b main`, but the workspace blocked `.git` writes. The
subsequent permission request was declined. No Git repository or initial commit
was created. Git initialization remains the next unfinished foundation step.

Once Git writes are allowed, the intended commands are:

```bash
git init -b main
git add .gitignore .python-version pyproject.toml uv.lock README.md docs src
git diff --cached
git commit -m "Initialize support agent lab with uv package and store tool"
```

Review the staged diff before committing. These commands create local history;
publishing to GitHub is a later checkpoint.

## 05 — Refund policy tool

Confirmed the user completed Git initialization and the initial commit
(`136f28a`). Added `.idea/` to `.gitignore` to exclude local IDE settings.

Created `src/support_agent_lab/policy.py` with `get_refund_policy()`. For this
fictional store, an existing order qualifies for a full refund when delivery is
at least two days late and it has not already been refunded. Exactly two days
qualifies. These are project rules, not a real retailer's policy.

The tool returns structured thresholds plus readable rules. It does not check
an order or issue a refund. The future refund tool will enforce these rules;
the agent will use them to explain its decision.

Verified the tool in the uv environment:

```bash
uv run python -c 'from support_agent_lab.policy import get_refund_policy; import json; print(json.dumps(get_refund_policy(), indent=2))'
```

Expected outcomes for our existing data: `ORD-001` qualifies for $80,
`ORD-002` does not qualify, and `ORD-003` cannot receive another refund.
These are expectations for the next implementation, not executed refund tests.

Next checkpoint: implement a simulated refund tool that enforces this policy.

## 06 — Simulated refund tool

Added `issue_refund(order_id)` to `store.py`. It rejects missing orders,
already-refunded orders, and deliveries below the policy's lateness threshold.
Only after these checks does it mark the order refunded and return the full
order price and policy ID. The caller cannot choose the refund amount.

The fake store holds state in memory. Repeating a refund in the same process
is rejected; starting another Python process resets the original sample data.
This is a single-process learning simulation, not a payment service.

Verified with a one-off Python assertion script in the uv environment:
eligible refund amount and state change, missing order, ineligible order with
unchanged state, already-refunded order, repeated refund, exactly two days late
(accepted), and one day late (rejected). All checks passed. Temporary boundary
fixtures existed only in that verification process.

Try the state change and duplicate protection in one process:

```bash
uv run python -c 'from support_agent_lab.store import issue_refund; print(issue_refund("ORD-001")); print(issue_refund("ORD-001"))'
```

Next checkpoint: turn these checks into repeatable pytest tests, with isolated
store state for each test, before connecting an LLM.

## 07 — Repeatable tool tests

Added pytest as a development dependency:

```bash
uv add --dev pytest --cache-dir .uv-cache
```

The sandbox initially blocked access to PyPI; the approved retry succeeded.
uv updated `pyproject.toml` and `uv.lock` and installed pytest in `.venv`.
pytest is needed for development, not for running the store tool.

Created `tests/test_store.py`. An automatic fixture uses `deepcopy` and pytest's
`monkeypatch` to replace the store for each test and restore it afterward.
Parameterized tests run the same check against multiple inputs.

```bash
uv run pytest -q
```

Verification: **10 passed**. Coverage includes lookup facts and missing orders,
lookup-result mutation isolation, full-price refund and target-only mutation,
rejected refunds with unchanged state, duplicate refunds, and the one-day versus
two-day eligibility boundary. These are deterministic tool tests, not agent
evaluations. Next: choose the model/provider and connect the agent to these tools.

## 08 — First Claude connection

Selected Anthropic because the user has an `ANTHROPIC_API_KEY` environment
variable. Installed the SDK with `uv add anthropic --cache-dir .uv-cache`
(network access required an approved retry). uv updated metadata and the lockfile.

Added `llm.py` with `ask_claude(prompt, model)` and a runnable module entry point.
It sends a single Messages API request, extracts text blocks, and closes the
client. Output is capped at 256 tokens, timeout is 30 seconds, and automatic
retries are disabled for this initial connection check. The model is configurable
with `--model`; the default is `claude-haiku-5-5` from Anthropic's model docs.

```bash
uv run python -m support_agent_lab.llm "Say hello in one sentence."
```

The key was not available in the assistant's shell. No live call was made;
the user must run this command from their configured terminal. Local verification
checks CLI help, missing-key handling, and the existing store tests. This is a
connection checkpoint, not yet a tool-calling agent.

## 09 — First agent tool loop

The user confirmed the live text-only command returned a greeting successfully.
Added `agent.py` as a separate checkpoint, preserving `llm.py` for comparison.
`ORDER_TOOL` describes the function and its input schema to Claude. `run_agent`
sends the conversation, executes requested lookups, and returns tool results
with the matching call ID. Claude can then answer or request another lookup.
The loop allows at most five model requests and rejects incomplete stop reasons.
Tool names and arguments are checked before execution. Console output exposes
calls and results; structured trace recording comes later.

```bash
uv run python -m support_agent_lab.agent "What happened to order ORD-001?"
```

Added offline tests for the tool-result round trip, the loop limit, and truncated
responses. `uv run pytest -q`: **13 passed**. These use a mock client and do not
establish real model behavior. Live tool-loop verification is pending the user
running the command in their terminal where the API key is available.

Reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview

## 10 — Connect policy and simulated refunds

The user verified live order lookup. Its answer also offered to record a note
for a team, although no such tool exists: a candidate failure for future evals.

Added policy and refund schemas to `agent.py`, plus `execute_tool` to validate
arguments and dispatch all three tools. Kept the existing manual conversation
loop and the user's stop-reason debug print. Updated the prompt to consult the
order and policy, distinguish eligibility questions from refund requests, report
only confirmed simulated refunds, and avoid offering unsupported actions.

Customer authorization and consulting the policy are model instructions at this
checkpoint. The tool enforces order existence, eligibility, and duplicate-refund
protection; the dispatcher does not independently verify customer intent.

Verification: `uv run pytest -q` reports **18 passed**. New tests verify malformed
requests leave the store unchanged and a mocked three-tool workflow returns the
right results and changes refund state. These do not prove the live model follows
the prompt. Next, compare these two live runs:

```bash
uv run python -m support_agent_lab.agent "Is ORD-001 eligible for a refund?"
uv run python -m support_agent_lab.agent "Please refund ORD-001 if eligible."
```

Only the second should call `issue_refund`. Both commands reset the in-memory
store on startup. After reviewing behavior, capture structured runs for evals.

## 11 — Commit working agent, then record runs

The user confirmed three live scenarios: eligible inquiry without a refund,
ineligible inquiry without a refund, and an explicit request producing an $80
simulated refund. Policy lookup preceded order lookup; either order is acceptable
as long as both checks precede the refund.

Committed the working agent and tests as `6d57940` before adding recording.

Added `recording.py`, which wraps the manual loop, measures elapsed time, and
writes a uniquely named JSON file in `runs/`. The loop accepts an optional trace
dictionary and appends model usage and tool execution details. The wrapper saves
the answer on success or partial progress and error type on failure, then
re-raises failures. It does not save exception messages or API credentials.

```bash
uv run python -m support_agent_lab.agent "Is ORD-001 eligible for a refund?"
```

Open the path printed after `[run] Saved`. Look for two tool calls, no
`issue_refund`, a completed status, and model response usage. Repeated runs get
separate files. Records are ignored by Git and contain customer prompts and tool
data. They are our first local trace format, not yet the article's toolkit format.

Verification: **20 tests passed**, including a saved successful round trip with
token totals and a failed second request preserving the first tool result. Tests
use mocked API responses. Live recording verification remains for the user.
Next checkpoint: define an evaluation scenario and check its saved trace.
