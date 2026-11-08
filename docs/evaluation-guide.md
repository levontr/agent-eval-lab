# Evaluation: concepts and project scope

## The pieces

- **Scenario:** an input, initial conditions, and expectations defined before execution.
- **Runner:** executes the agent on scenarios, resetting state between cases.
- **Trace:** evidence of what actually happened (calls, results, timing, usage).
- **Evaluator:** applies expectations to that evidence.
- **Experiment:** a collection of runs and scores for one agent configuration.

Our scenario JSON is our own format. OpenTelemetry provides span timing, IDs,
relationships, and export. OpenInference supplies AI conventions and integrations.
Neither decides what correct business behavior means.

## Development and release workflow

Keep a versioned scenario set. After changing prompts, models, or agent code,
execute the changed agent to generate new traces and compare evaluation results.
Regrading old traces tests an evaluator or reexamines old behavior; it cannot
establish that changed agent code works. Add cases for new requirements and bugs;
do not silently weaken old expectations to make a change pass.

Run the same suite locally and, eventually, in a CI job. Fast deterministic
tests can run on every change. Live model suites need credentials and budgets;
run selected cases before merging and broader/repeated experiments as appropriate.
Offline evaluation means controlled test data outside production traffic, not
necessarily disconnected from the internet. Test tools must use isolated fixtures
or a sandbox, not issue real payments. Reset state before each case.

Record code revision, model, prompt, dataset, and evaluator versions for comparisons.
Repeat important cases because one passing model response is not proof of reliability.
Use critical pass/fail rules and measured quality thresholds suited to the application.

## Production feedback

Production traces can be evaluated afterward, in background jobs or batches.
Code can check precise rules; human reviewers or validated LLM judges can assess
interpretive questions. Real traffic usually lacks prewritten reference answers.
Sampling controls evaluation cost. Selected, sanitized failures can become new
regression scenarios with explicit expectations and reproducible initial data.

Post-execution evaluation detects failures; it does not prevent an action already
taken. Required authorization and other hard constraints belong in execution logic.

## Judges and frameworks

Use code for exact rules (tool names, arguments, counts, amounts). Use an LLM judge
when interpretation is required, validating it against human-labeled examples.
Both offline and production evaluation may combine code, judges, and human review.
A judge can be a separate API call; LangChain is not required. Evaluation platforms
help manage datasets, runs, and reports, but do not define our requirements for us.

## What belongs in Git

Commit scenario definitions, synthetic fixtures, evaluators, agent code, prompts,
dependency locks, and CI configuration. Save routine traces/reports as experiment
artifacts rather than source files. Small reviewed traces may be committed as
evaluator test fixtures. Review recorded customer data before sharing it.

## Our scope

Implemented: a small agent, isolated offline tests, local recording, automatic
model spans, explicit tool spans, and a single-run deterministic evaluator.
A three-scenario dataset and sequential local runner are also implemented.
Optional later: CI, a trace viewer, an evaluation toolkit, repeated experiments,
and LLM judging. This project has no production traffic or live payment service.

## References discussed

- [Evaluation lifecycle](https://docs.langchain.com/langsmith/evaluation)
- [Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
- [OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/)
- [OpenInference](https://arize-ai.github.io/openinference/)

The LangSmith references explain the concepts; they are not project dependencies.
