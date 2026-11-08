"""OpenTelemetry spans with OpenInference attributes, exported locally."""

from contextlib import contextmanager
from contextvars import ContextVar

from openinference.instrumentation.anthropic import AnthropicInstrumentor
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
        instrumentor = AnthropicInstrumentor()
        owns_instrumentation = False
        try:
            if instrumentor.is_instrumented_by_opentelemetry:
                raise RuntimeError("Anthropic tracing is already configured; concurrent recorded runs are not supported.")
            instrumentor.instrument(tracer_provider=provider)
            owns_instrumentation = True
            with operation("support_agent", "AGENT") as span:
                span.set_attribute(Attr.INPUT_VALUE, prompt)
                yield span
        finally:
            if owns_instrumentation:
                instrumentor.uninstrument()
            provider.shutdown()
            _tracer.reset(token)
