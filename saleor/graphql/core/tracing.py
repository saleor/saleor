from functools import wraps

from graphene import ResolveInfo

from ...core.telemetry import saleor_attributes, tracer


def traced_resolver(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        info = next(arg for arg in args if isinstance(arg, ResolveInfo))
        operation = f"{info.parent_type.name}.{info.field_name}"
        with tracer.start_as_current_span(operation) as span:
            span.set_attribute(saleor_attributes.OPERATION_NAME, "graphql.resolve")
            span.set_attribute(
                saleor_attributes.GRAPHQL_PARENT_TYPE, info.parent_type.name
            )
            span.set_attribute(saleor_attributes.GRAPHQL_FIELD_NAME, info.field_name)
            return func(*args, **kwargs)

    return wrapper
