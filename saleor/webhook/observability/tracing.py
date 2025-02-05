from contextlib import contextmanager

import opentracing


@contextmanager
def opentracing_trace(span_name, component):
    with opentracing.global_tracer().start_active_span(
        f"observability.{span_name}"
    ) as scope:
        span = scope.span
        span.set_tag("service.name", "observability")
        span.set_tag(opentracing.tags.COMPONENT, component)
        yield


# TODO: Remove after performing load tests!
@contextmanager
def load_tests_breaker_opentracing_trace(span_name, component):
    with opentracing.global_tracer().start_active_span(f"breaker.{span_name}") as scope:
        span = scope.span
        span.set_tag("service.name", "webhooks")
        span.set_tag(opentracing.tags.COMPONENT, component)
        yield
