from collections.abc import Generator
from contextlib import contextmanager

from opentelemetry import trace as otel_trace
from opentelemetry.trace import Span, SpanKind
from opentelemetry.util.types import Attributes

from .context import enrich_with_trace_attributes


class Tracer:
    def __init__(self, internal_scope: str, public_scope: str, version: str) -> None:
        self._internal_tracer = otel_trace.get_tracer(internal_scope, version)
        self._public_tracer = otel_trace.get_tracer(public_scope, version)

    def _otel_tracer(self, internal: bool):
        return self._internal_tracer if internal else self._public_tracer

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        *,
        internal: bool = True,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
    ) -> Generator[Span, None, None]:
        attributes = enrich_with_trace_attributes(attributes)
        tracer = self._otel_tracer(internal)
        with tracer.start_as_current_span(
            name, kind=kind, attributes=attributes
        ) as span:
            yield span

    def start_span(
        self,
        name: str,
        *,
        internal: bool = True,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
    ) -> Span:
        attributes = enrich_with_trace_attributes(attributes)
        tracer = self._otel_tracer(internal)
        return tracer.start_span(name, kind=kind, attributes=attributes)

    def get_current_span(self) -> Span:
        return otel_trace.get_current_span()
