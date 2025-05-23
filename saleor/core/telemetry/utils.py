import logging
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

from django.conf import settings
from opentelemetry.trace import Link, SpanContext, TraceFlags
from opentelemetry.util.types import Attributes, AttributeValue

from .saleor_attributes import OPERATION_NAME

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
    BYTE = "By"
    COST = "{cost}"


UNIT_CONVERSIONS: dict[tuple[Unit, Unit], float] = {
    (Unit.NANOSECOND, Unit.MILLISECOND): 1e-6,
    (Unit.NANOSECOND, Unit.SECOND): 1e-9,
    (Unit.SECOND, Unit.MILLISECOND): 1e3,
}


def convert_unit(amount: Amount, unit: Unit, to_unit: Unit) -> Amount:
    if unit == to_unit:
        return amount
    try:
        return amount * UNIT_CONVERSIONS[(unit, to_unit)]
    except KeyError as e:
        msg = f"Conversion from {unit} to {to_unit} not supported"
        if settings.TELEMETRY_RAISE_UNIT_CONVERSION_ERRORS:
            raise ValueError(msg) from e
        logger.error(msg, exc_info=e)
    return amount


@contextmanager
def set_global_attributes(attributes: dict[str, AttributeValue]):
    token = _GLOBAL_ATTRS.set(attributes)
    try:
        yield
    finally:
        _GLOBAL_ATTRS.reset(token)


def get_global_attributes() -> dict[str, AttributeValue]:
    return _GLOBAL_ATTRS.get({})


def enrich_with_global_attributes(attributes: Attributes) -> dict[str, AttributeValue]:
    return {**(attributes or {}), **get_global_attributes()}


def enrich_span_with_global_attributes(
    attributes: Attributes, span_name: str
) -> dict[str, AttributeValue]:
    return {OPERATION_NAME: span_name, **enrich_with_global_attributes(attributes)}


@dataclass(frozen=True)
class TelemetryTaskContext:
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
                    "attributes": dict(link.attributes) if link.attributes else {},
                }
                for link in (self.links or [])
            ],
            "global_attributes": dict(self.global_attributes),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "TelemetryTaskContext":
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
    """Handle telemetry context injection for Celery tasks.

    This decorator deserializes the telemetry context and sets the global attributes for the task execution.
    The decorated function must accept a 'telemetry_context: TelemetryTaskContext' kwarg and it is
    recommended to invoke the task with 'telemetry_context=get_task_context().to_dict()'.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        context = TelemetryTaskContext(global_attributes={})
        if "telemetry_context" not in kwargs:
            logger.warning("No telemetry_context provided for the task")
        else:
            try:
                context = TelemetryTaskContext.from_dict(
                    kwargs.pop("telemetry_context")
                )
            except ValueError:
                logger.exception("Failed to parse telemetry context")

        with set_global_attributes(context.global_attributes):
            return func(*args, telemetry_context=context, **kwargs)

    return wrapper
