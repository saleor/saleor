from contextlib import contextmanager
from contextvars import ContextVar

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
