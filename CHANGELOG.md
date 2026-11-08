# Changelog

## Publication preparation

Shortened the docs, removed stale checkpoint descriptions, and added an offline
GitHub Actions workflow. No agent behavior changed.

## 2026-11-08

- Added a separate refund-outcome judge with a JSON response schema.
- Added four labeled synthetic examples and a batch judge check; live batch matched 4/4.
- Demonstrated prompt regression and recovery: 3/3 → 2/3 → 3/3 scenarios passed.
- Added a sequential scenario runner with fresh store state and saved reports.
- Replaced manual model-call spans with OpenInference's Anthropic instrumentor.
- Kept explicit agent/tool spans and custom JSON summaries.

## Initial implementation

Added uv packaging, fictional store tools, a bounded Claude tool loop, and offline
tests. See the [build history](docs/build-journal.md) for commit references.
