from contextlib import contextmanager

from django.db import transaction
from opentelemetry import trace

from ..core.otel import public_tracer, tracer


@contextmanager
def traced_atomic_transaction():
    with transaction.atomic():
        with tracer.start_as_current_span("transaction") as span:
            span.set_attribute("component", "orm")
            yield


@contextmanager
def otel_trace(span_name, component_name, service_name):
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("component", component_name)
        span.set_attribute("service.name", service_name)
        yield


@contextmanager
def webhooks_otel_trace(
    span_name,
    domain,
    payload_size: int,
    sync=False,
    app=None,
):
    """Context manager for tracing webhooks.

    :param payload_size: size of the payload in bytes
    """
    with tracer.start_as_current_span(
        f"webhooks.{span_name}", kind=trace.SpanKind.CLIENT
    ) as span:
        if app:
            span.set_attribute("app.id", app.id)
            span.set_attribute("app.name", app.name)
        span.set_attribute("component", "webhooks")
        span.set_attribute("service.name", "webhooks")
        span.set_attribute("webhooks.domain", domain)
        span.set_attribute("webhooks.execution_mode", "sync" if sync else "async")
        span.set_attribute("webhooks.payload_size", payload_size)
        yield


@contextmanager
def public_webhooks_otel_trace(
    span_name,
    domain,
    payload_size: int,
    sync=False,
    app=None,
    public_span_ctx: trace.SpanContext | None = None,
):
    public_span = None
    if public_span_ctx:
        span_parent = trace.set_span_in_context(trace.NonRecordingSpan(public_span_ctx))
        public_span = public_tracer.start_span(
            f"webhooks.{span_name}", kind=trace.SpanKind.CLIENT, context=span_parent
        )

    with tracer.start_as_current_span(
        f"webhooks.{span_name}", kind=trace.SpanKind.CLIENT
    ) as span:
        if app:
            span.set_attribute("app.id", app.id)
            span.set_attribute("app.name", app.name)
        span.set_attribute("component", "webhooks")
        span.set_attribute("service.name", "webhooks")
        span.set_attribute("webhooks.domain", domain)
        span.set_attribute("webhooks.execution_mode", "sync" if sync else "async")
        span.set_attribute("webhooks.payload_size", payload_size)

        yield

    if public_span:
        public_span.end()
