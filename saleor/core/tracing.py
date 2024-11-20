from contextlib import contextmanager

import opentracing
from django.db import transaction


@contextmanager
def traced_atomic_transaction():
    with transaction.atomic():
        with opentracing.global_tracer().start_active_span("transaction") as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "orm")
            yield


@contextmanager
def opentracing_trace(span_name, component_name, service_name):
    with opentracing.global_tracer().start_active_span(span_name) as scope:
        span = scope.span
        span.set_tag(opentracing.tags.COMPONENT, component_name)
        span.set_tag("service.name", service_name)
        yield


@contextmanager
def webhooks_opentracing_trace(
    span_name,
    domain,
    payload_size: int,
    sync=False,
    app=None,
):
    """Context manager for tracing webhooks.

    :param payload_size: size of the payload in bytes
    """
    with opentracing.global_tracer().start_active_span(
        f"webhooks.{span_name}"
    ) as scope:
        span = scope.span
        if app:
            span.set_tag("app.id", app.id)
            span.set_tag("app.name", app.name)
        span.set_tag(opentracing.tags.COMPONENT, "webhooks")
        span.set_tag("service.name", "webhooks")
        span.set_tag("webhooks.domain", domain)
        span.set_tag("webhooks.execution_mode", "sync" if sync else "async")
        span.set_tag("webhooks.payload_size", payload_size)
        yield
