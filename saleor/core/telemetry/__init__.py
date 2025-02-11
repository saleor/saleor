from django.conf import settings
from opentelemetry.semconv.trace import SpanAttributes

from .metric import Meter, MeterProxy, MetricType, Unit, load_meter
from .trace import SpanKind, Tracer, TracerProxy, load_tracer
from .utils import set_global_attributes

_tracer = TracerProxy()
_meter = MeterProxy()
tracer: Tracer = _tracer
meter: Meter = _meter


def initialize_telemetry() -> None:
    if not settings.TELEMETRY_ENABLED:
        return
    _tracer.initialize(load_tracer())
    _meter.initialize(load_meter())


__all__ = [
    "tracer",
    "meter",
    "initialize_telemetry",
    "set_global_attributes",
    "Unit",
    "MetricType",
    "SpanKind",
    "SpanAttributes",
]
