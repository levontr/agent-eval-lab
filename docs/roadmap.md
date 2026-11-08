# Roadmap

Build one reviewable checkpoint at a time. Each checkpoint should include an
explanation, runnable code or commands, appropriate verification, and a journal
entry. Planned items below are not implemented yet.

| Checkpoint | Deliverable | Status |
| --- | --- | --- |
| Project setup | uv environment, lockfile, README | Complete |
| First tool | Fake orders and order lookup | Complete |
| Repository foundation | Python package layout and local Git history | Complete |
| Store behavior | Explicit refund policy and simulated refund tool | Complete |
| Tool tests | Deterministic tests for eligibility and duplicate refunds | Complete (10 passing cases) |
| Agent | LLM tool-calling loop and CLI; documented API key setup | Complete; live eligibility and refund scenarios verified by user |
| Tracing | Tool arguments, results, final responses, timing, token usage | JSON recording verified live; OpenTelemetry/OpenInference spans added and tested offline |
| Automatic instrumentation | Replace manual model-call spans with the Anthropic integration | Complete; verified with real SDK and fake HTTP responses; live run next |
| Evaluation | Fixed scenarios, expected outcomes, trace checks, toolkit integration | Planned |
| Experiment | Baseline versus one agent change, with measured results | Planned |
| Publication | CI, reproducible demo, limitations, and GitHub publishing | Planned |

## What the finished portfolio should demonstrate

- A working support agent over a fictional store.
- Correct, independently tested tools.
- Evaluation of outcomes and execution, including duplicate actions and failures.
- An understandable report showing what improved or regressed after a change.
- Setup instructions another developer can follow.

Start with manually reviewed runs before adding automated judges. Select and
verify the article's evaluation tooling at the integration checkpoint, including
its dependencies, account requirements, and any service costs.

Keep ordinary software tests distinct from agent evaluations: tests verify tool
logic; evaluations measure whether the model uses those tools appropriately.
