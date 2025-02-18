from ..core.telemetry import tracer


def traced_payload_generator(func):
    def wrapper(*args, **kwargs):
        operation = f"{func.__name__}"
        with tracer.start_as_current_span(operation) as span:
            span.set_attribute("component", "payloads")
            return func(*args, **kwargs)

    return wrapper
