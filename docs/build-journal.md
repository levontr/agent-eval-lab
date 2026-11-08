# Build history

The project grew in small steps. Earlier, more detailed notes remain in Git history.

| Commit | Step | What it established |
| --- | --- | --- |
| `136f28a` | Python package and uv setup | A runnable order lookup |
| `6d57940` | Agent and store tools | Claude can inspect orders and request simulated refunds |
| `e89114f` | JSON recording | Runs can be inspected after execution |
| `c0bdaf0` | Manual OpenTelemetry spans | Agent, model, and tool operations have parent/child relationships |
| `b9905fd` | Automatic Anthropic instrumentation | Model spans no longer need a custom wrapper |
| `1438323` | First evaluator | An eligibility-only question must not trigger a refund |
| `f626c08` | Three-scenario runner | Fresh store state and one combined report per experiment |
| `eef34c3` | Regression experiment | Changing the prompt produced an unwanted refund; restoring it recovered the baseline |
| `b542323` | Separate answer judge | Correct tool behavior does not guarantee a truthful final answer |

## Decisions

The agent loop stays explicit so its behavior is easy to follow. The judge remains
separate from the runner so ordinary scenario checks do not incur judging costs.
Both custom run summaries and OpenTelemetry spans are kept: the evaluator reads
the summaries, while the spans show timing and execution structure.

The Google evaluation toolkit from the article was considered but not integrated.
The current project uses the Anthropic SDK, OpenTelemetry, OpenInference, and Python
checks. CI runs offline tests only.

See [results](results.md) for the observed experiments and [evaluation notes](evaluation-guide.md)
for the concepts behind them.
