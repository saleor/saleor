from contextlib import contextmanager
from contextvars import ContextVar
from importlib import import_module
from typing import Any

from opentelemetry.util.types import Attributes, AttributeValue

_global_attrs: ContextVar[dict[str, AttributeValue]] = ContextVar("global_attrs")


@contextmanager
def set_global_attributes(attributes: dict[str, AttributeValue]):
    token = _global_attrs.set(attributes)
    try:
        yield
    finally:
        _global_attrs.reset(token)


def enrich_with_global_attributes(attributes: Attributes) -> Attributes:
    trace_attributes = _global_attrs.get({})
    return {**(attributes or {}), **trace_attributes}


def load_object(python_path: str) -> Any:
    module, obj = python_path.rsplit(".", 1)
    return getattr(import_module(module), obj)
