"""Custom context management for telemetry.

This module provides a custom context implementation for storing and managing trace
attributes independently of OpenTelemetry's built-in context. This approach is
necessary when working with third-party libraries (e.g., ddtrace) that provide
their own SDK implementations and may modify the default context behavior, making
it unable to store additional information beyond OpenTelemetry's standard use cases.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import cast

from opentelemetry.trace import Tracer
from opentelemetry.util.types import Attributes, AttributeValue

_trace_attributes: ContextVar[dict[str, AttributeValue]] = ContextVar(
    "trace_attributes"
)


@contextmanager
def set_trace_attributes(attributes: dict[str, AttributeValue]):
    token = _trace_attributes.set(attributes)
    try:
        yield
    finally:
        _trace_attributes.reset(token)


def get_trace_attributes() -> dict[str, AttributeValue]:
    try:
        return _trace_attributes.get()
    except LookupError as err:
        raise RuntimeError("Trace attributes not set.") from err


def enrich_with_trace_attributes(attributes: Attributes) -> dict[str, AttributeValue]:
    trace_attributes = get_trace_attributes()
    if not attributes:
        return trace_attributes
    return {**attributes, **trace_attributes}


class ContextAwareTracer:
    def __init__(self, tracer: Tracer):
        self._tracer = tracer

    def start_span(self, *args, attributes: Attributes = None, **kwargs):
        attributes = enrich_with_trace_attributes(attributes)
        return self._tracer.start_span(*args, **dict(kwargs, attributes=attributes))

    @contextmanager
    def start_as_current_span(self, *args, attributes: Attributes = None, **kwargs):
        attributes = enrich_with_trace_attributes(attributes)
        with self._tracer.start_as_current_span(
            *args, **dict(kwargs, attributes=attributes)
        ) as span:
            yield span

    @classmethod
    def wrap(cls, tracer: Tracer) -> Tracer:
        return cast(Tracer, cls(tracer))
