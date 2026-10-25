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
