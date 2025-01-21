from contextlib import contextmanager

from ...core.otel import tracer


@contextmanager
def otel_trace(span_name, component):
    with tracer.start_as_current_span(f"observability.{span_name}") as span:
        span.set_attribute("service.name", "observability")
        span.set_attribute("component", component)
        yield
