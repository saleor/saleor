from importlib import import_module
from typing import Any

from django.conf import settings
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.util.types import AttributeValue

from .metric import Meter, MeterProxy, MetricType
from .trace import SpanKind, Tracer, TracerProxy
from .utils import Scope, Unit, set_global_attributes

tracer = TracerProxy()
meter = MeterProxy()


def load_object(python_path: str) -> Any:
    module, obj = python_path.rsplit(".", 1)
    return getattr(import_module(module), obj)


def initialize_telemetry() -> None:
    """Initialize telemetry components lazily to ensure fork safety in multi-process environments."""

    # To avoid circular imports.
    from ... import __version__ as saleor_version

    tracer_cls = load_object(settings.TELEMETRY_TRACER_CLASS)
    if not issubclass(tracer_cls, Tracer):
        raise ValueError(
            "settings.TELEMETRY_TRACER_CLASS must point to a subclass of Tracer"
        )
    tracer.initialize(tracer_cls, saleor_version)

    meter_cls = load_object(settings.TELEMETRY_METER_CLASS)
    if not issubclass(meter_cls, Meter):
        raise ValueError(
            "settings.TELEMETRY_METER_CLASS must point to a subclass of Meter"
        )
    meter.initialize(meter_cls, saleor_version)


__all__ = [
    "tracer",
    "meter",
    "initialize_telemetry",
    "set_global_attributes",
    "Unit",
    "MetricType",
    "SpanKind",
    "SpanAttributes",
    "AttributeValue",
    "Scope",
]
