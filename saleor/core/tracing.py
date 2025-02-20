from collections.abc import Sequence
from contextlib import contextmanager

from django.db import transaction

from ..core.telemetry import Link, Scope, SpanKind, tracer


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
    span_links: Sequence[Link] | None = None,
):
    """Context manager for tracing webhooks.

    :param payload_size: size of the payload in bytes
    """
    with tracer.start_as_current_span(
        f"webhooks.{span_name}",
        scope=Scope.SERVICE,
        kind=SpanKind.CLIENT,
        links=span_links,
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
