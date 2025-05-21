import uuid
from importlib import import_module
from typing import Any

from opentelemetry.sdk._configuration import _OTelSDKConfigurator
from opentelemetry.sdk.resources import SERVICE_INSTANCE_ID
from opentelemetry.util.types import Attributes

from .metric import DEFAULT_DURATION_BUCKETS, Meter, MeterProxy, MetricType
from .trace import Link, SpanKind, Tracer, TracerProxy
from .utils import (
    Scope,
    TelemetryTaskContext,
    Unit,
    set_global_attributes,
    task_with_telemetry_context,
)

tracer = TracerProxy()
meter = MeterProxy()


def load_object(python_path: str) -> Any:
    module, obj = python_path.rsplit(".", 1)
    return getattr(import_module(module), obj)


def otel_configure_sdk():
    configurator = _OTelSDKConfigurator()
    configurator.configure(resource_attributes={SERVICE_INSTANCE_ID: str(uuid.uuid4())})


def initialize_telemetry() -> None:
    """Initialize telemetry components lazily to ensure fork safety in multi-process environments."""
    otel_configure_sdk()

    # To avoid importing Django before instrumenting libs
    from django.conf import settings

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


def get_task_context(link_attributes: Attributes = None) -> TelemetryTaskContext:
    """Create telemetry task context with a link to the current span."""
    link = Link(tracer.get_current_span().get_span_context(), link_attributes)
    return TelemetryTaskContext(links=[link])


__all__ = [
    "tracer",
    "meter",
    "initialize_telemetry",
    "set_global_attributes",
    "Unit",
    "MetricType",
    "SpanKind",
    "Scope",
    "Link",
    "TelemetryTaskContext",
    "task_with_telemetry_context",
    "get_task_context",
    "DEFAULT_DURATION_BUCKETS",
]
