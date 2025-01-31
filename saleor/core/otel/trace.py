from typing import cast

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace import SpanKind, Tracer
from opentelemetry.util.types import Attributes

from ... import __version__
from .context import enrich_with_trace_attributes


class _ContextAwareTracer(Tracer):
    def __init__(self, tracer: Tracer):
        self._tracer = tracer

    def start_span(
        self,
        name: str,
        context: Context | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        *args,
        **kwargs,
    ):
        attributes = enrich_with_trace_attributes(attributes)
        return self._tracer.start_span(
            name,
            context,
            kind,
            attributes,
            *args,
            **kwargs,
        )

    def start_as_current_span(
        self,
        name: str,
        context: Context | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        *args,
        **kwargs,
    ):
        attributes = enrich_with_trace_attributes(attributes)
        return self._tracer.start_as_current_span(
            name, context, kind, attributes, *args, **kwargs
        )


def get_tracer(scope_name: str) -> Tracer:
    tracer = trace.get_tracer(scope_name, __version__)
    return cast(Tracer, _ContextAwareTracer(tracer))
