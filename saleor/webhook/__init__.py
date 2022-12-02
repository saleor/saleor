import opentracing


def traced_payload_generator(func):
    def wrapper(*args, **kwargs):
        operation = f"{func.__name__}"
        with opentracing.global_tracer().start_active_span(operation) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "payloads")
            return func(*args, **kwargs)

    return wrapper
