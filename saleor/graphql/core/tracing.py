from functools import wraps

from graphene import ResolveInfo

from ...core.telemetry import tracer


def traced_resolver(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = next(arg for arg in args if isinstance(arg, ResolveInfo))
        operation = f"{info.parent_type.name}.{info.field_name}"
        with tracer.start_as_current_span("graphql.resolve") as span:
            span.set_attribute("resource.name", operation)
            span.set_attribute("graphql.parent_type", info.parent_type.name)
            span.set_attribute("graphql.field_name", info.field_name)
            return func(*args, **kwargs)

    return wrapper
