import logging
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

from opentelemetry.trace import Link, SpanContext, TraceFlags
from opentelemetry.util.types import Attributes, AttributeValue

logger = logging.getLogger(__name__)

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


@dataclass(frozen=True)
class TelemetryContext:
    """Carries telemetry context when propagated to Celery tasks."""

    # TODO add TraceState support
    links: Sequence[Link] | None = None
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
                for link in (self.links or [])
            ],
            "global_attributes": dict(self.global_attributes),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "TelemetryContext":
        if not data:
            return cls(global_attributes={})
        try:
            links = [
                Link(
                    context=SpanContext(
                        trace_id=link["context"]["trace_id"],
                        span_id=link["context"]["span_id"],
                        is_remote=True,
                        trace_flags=TraceFlags(link["context"]["trace_flags"]),
                    ),
                    attributes=link.get("attributes"),
                )
                for link in data.get("links", [])
            ]
            return cls(links=links, global_attributes=data.get("global_attributes", {}))
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid telemetry context data: {e}") from e


def task_with_telemetry_context(func: Callable) -> Callable:
    """Propagate telemetry context to Celery tasks.

    Sets global attributes within task context. Wrapped function must accept span_links kwarg.
    Task must be invoked with telemetry_context kwarg.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        context = TelemetryContext(global_attributes={})
        if "telemetry_context" not in kwargs:
            logger.warning("No telemetry_context provided for the task")
        else:
            try:
                context = TelemetryContext.from_dict(kwargs.pop("telemetry_context"))
            except ValueError:
                logger.exception("Failed to parse telemetry context")

        with set_global_attributes(context.global_attributes):
            return func(*args, span_links=context.links, **kwargs)

    return wrapper
