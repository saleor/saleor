from collections.abc import Sequence
from contextlib import contextmanager

from django.db import transaction

from ..app.models import App
from ..core.telemetry import Link, Scope, SpanKind, saleor_attributes, tracer


@contextmanager
def traced_atomic_transaction():
    with transaction.atomic():
        with tracer.start_as_current_span("transaction") as span:
            span.set_attribute(saleor_attributes.COMPONENT, "orm")
            yield


@contextmanager
def otel_trace(span_name, component_name):
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute(saleor_attributes.COMPONENT, component_name)
        yield


@contextmanager
def webhooks_otel_trace(
    event_type: str,
    payload_size: int,
    sync=False,
    app: App | None = None,
    span_links: Sequence[Link] | None = None,
):
    """Context manager for tracing webhooks.

    :param payload_size: size of the payload in bytes
    """
    with tracer.start_as_current_span(
        f"webhooks.{event_type}",
        scope=Scope.SERVICE,
        kind=SpanKind.CLIENT,
        links=span_links,
    ) as span:
        if app:
            span.set_attribute(saleor_attributes.SALEOR_APP_ID, app.id)
            span.set_attribute(saleor_attributes.SALEOR_APP_NAME, app.name)
        span.set_attribute(saleor_attributes.COMPONENT, "webhooks")
        span.set_attribute(
            saleor_attributes.SALEOR_WEBHOOK_EXECUTION_MODE, "sync" if sync else "async"
        )
        span.set_attribute(saleor_attributes.SALEOR_WEBHOOK_PAYLOAD_SIZE, payload_size)
        yield span
