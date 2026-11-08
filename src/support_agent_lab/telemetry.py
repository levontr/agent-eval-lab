"""OpenTelemetry spans with OpenInference attributes, exported locally."""

from contextlib import contextmanager
from contextvars import ContextVar

from openinference.semconv.trace import SpanAttributes as Attr
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import StatusCode


_tracer = ContextVar("agent_tracer", default=trace.NoOpTracer())


@contextmanager
def operation(name: str, kind: str):
    """Open a timed operation; OpenTelemetry connects it to its active parent."""
    with _tracer.get().start_as_current_span(
        name,
        attributes={Attr.OPENINFERENCE_SPAN_KIND: kind},
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            yield span
        except Exception as error:
            span.set_attribute("error.type", type(error).__name__)
            span.set_status(StatusCode.ERROR)
            raise


@contextmanager
def trace_run(path, prompt: str):
    """Use a provider scoped to one run; no global setup or remote server."""
    with path.open("w", encoding="utf-8") as output:
        provider = TracerProvider(resource=Resource.create({"service.name": "support-agent-lab"}))
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter(
            out=output, formatter=lambda span: span.to_json(indent=None) + "\n"
        )))
        token = _tracer.set(provider.get_tracer("support_agent_lab"))
        try:
            with operation("support_agent", "AGENT") as span:
                span.set_attribute(Attr.INPUT_VALUE, prompt)
                yield span
        finally:
            provider.shutdown()
            _tracer.reset(token)


def call_model(client, **kwargs):
    """Trace one SDK request while leaving conversation management in agent.py."""
    with operation("anthropic.messages.create", "LLM") as span:
        span.set_attribute(Attr.LLM_MODEL_NAME, kwargs["model"])
        response = client.messages.create(**kwargs)
        span.set_attribute("llm.finish_reason", response.stop_reason)
        usage = getattr(response, "usage", None)
        for field, attribute in [
            ("input_tokens", Attr.LLM_TOKEN_COUNT_PROMPT),
            ("output_tokens", Attr.LLM_TOKEN_COUNT_COMPLETION),
        ]:
            value = getattr(usage, field, None)
            if isinstance(value, int):
                span.set_attribute(attribute, value)
        return response
