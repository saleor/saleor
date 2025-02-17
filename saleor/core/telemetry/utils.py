from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any

from opentelemetry.trace import Link, SpanContext
from opentelemetry.util.types import Attributes, AttributeValue

Amount = int | float

_GLOBAL_ATTRS: ContextVar[dict[str, AttributeValue]] = ContextVar("global_attrs")


class Scope(Enum):
    CORE = "saleor.core"
    SERVICE = "saleor.service"

    @property
    def is_service(self):
        return self == Scope.SERVICE


class Unit(Enum):
    SECOND = "s"
    MILLISECOND = "ms"
    NANOSECOND = "ns"
    REQUEST = "{request}"


UNIT_CONVERSIONS: dict[tuple[Unit, Unit], float] = {
    (Unit.NANOSECOND, Unit.MILLISECOND): 1e-6,
    (Unit.NANOSECOND, Unit.SECOND): 1e-9,
}


def convert_unit(amount: Amount, unit: Unit | None, to_unit: Unit) -> Amount:
    if unit is None or unit == to_unit:
        return amount
    try:
        return amount * UNIT_CONVERSIONS[(unit, to_unit)]
    except KeyError as e:
        raise ValueError(f"Conversion from {unit} to {to_unit} not supported") from e


@contextmanager
def set_global_attributes(attributes: dict[str, AttributeValue]):
    token = _GLOBAL_ATTRS.set(attributes)
    try:
        yield
    finally:
        _GLOBAL_ATTRS.reset(token)


def get_global_attributes() -> dict[str, AttributeValue]:
    return _GLOBAL_ATTRS.get({})


def enrich_with_global_attributes(attributes: Attributes) -> Attributes:
    return {**(attributes or {}), **get_global_attributes()}


@dataclass
class TaskTelemetryContext:
    links: list[Link] = field(default_factory=list)
    global_attributes: dict[str, AttributeValue] = field(
        default_factory=get_global_attributes
    )

    def to_dict(self) -> dict:
        return {
            "links": [
                {
                    "context": {
                        "trace_id": link.context.trace_id,
                        "span_id": link.context.span_id,
                        "trace_flags": int(link.context.trace_flags),
                    },
                    "attributes": link.attributes,
                }
                for link in self.links
            ],
            "global_attributes": dict(self.global_attributes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskTelemetryContext":
        links = [
            Link(
                context=SpanContext(
                    trace_id=link["context"]["trace_id"],
                    span_id=link["context"]["span_id"],
                    is_remote=True,
                    trace_flags=link["context"]["trace_flags"],
                ),
                attributes=link.get("attributes"),
            )
            for link in data["links"]
        ]
        return cls(links=links, global_attributes=data["global_attributes"])


def with_telemetry_context(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        context = TaskTelemetryContext()
        if context_data := kwargs.pop("telemetry_context", {}):
            if isinstance(context_data, TaskTelemetryContext):
                context = context_data
            else:
                context = TaskTelemetryContext.from_dict(context_data)
        kwargs["telemetry_context"] = context
        with set_global_attributes(context.global_attributes):
            return func(*args, **kwargs)

    return wrapper
