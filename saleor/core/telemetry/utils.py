from contextlib import contextmanager
from contextvars import ContextVar
from enum import Enum

from opentelemetry.util.types import Attributes, AttributeValue

Amount = int | float

_GLOBAL_ATTRS: ContextVar[dict[str, AttributeValue]] = ContextVar("global_attrs")


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


def enrich_with_global_attributes(attributes: Attributes) -> Attributes:
    trace_attributes = _GLOBAL_ATTRS.get({})
    return {**(attributes or {}), **trace_attributes}
