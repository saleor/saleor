import logging
import uuid
from collections.abc import Iterable
from importlib import import_module
from importlib.metadata import entry_points
from typing import Any

from opentelemetry.metrics import NoOpMeterProvider
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

logger = logging.getLogger(__name__)

tracer = TracerProxy()
meter = MeterProxy()


def load_object(python_path: str) -> Any:
    module, obj = python_path.rsplit(".", 1)
    return getattr(import_module(module), obj)


def otel_configure_sdk():
    configurator = _OTelSDKConfigurator()
    configurator.configure(resource_attributes={SERVICE_INSTANCE_ID: str(uuid.uuid4())})


def instrument_libraries(names: Iterable[str]) -> None:
    """Enable the OpenTelemetry library instrumentors with the given entry point names.

    Names come from the `opentelemetry_instrumentor` entry point group that every
    opentelemetry-instrumentation-* package registers, for example `psycopg` or
    `celery`. A name that cannot be found or set up is logged and skipped, so a
    telemetry problem never stops the process from starting. An instrumentor that
    was already set up by something else (for example the `opentelemetry-instrument`
    wrapper) is left as it is and reported, since its tracer and meter providers
    were then chosen by that other party.
    """
    # Library instrumentors are used for spans only, their metrics are discarded on
    # purpose by handing them a no-op MeterProvider. Saleor owns what goes to the
    # metric pipeline: the requests instrumentor would duplicate the webhook request
    # metrics recorded in saleor.webhook.transport.metrics, with extra port and
    # status dimensions multiplying the series, and the Celery task runtime histogram
    # is not needed. Keeping the metric set fixed also keeps its cost predictable.
    meter_provider = NoOpMeterProvider()
    enabled = []
    for name in names:
        matches = entry_points(group="opentelemetry_instrumentor", name=name)
        if not matches:
            logger.error("Telemetry instrumentor not found: %s", name)
            continue
        try:
            instrumentor = next(iter(matches)).load()()
            if instrumentor.is_instrumented_by_opentelemetry:
                logger.warning(
                    "Telemetry instrumentor already set up outside Saleor: %s", name
                )
                continue
            instrumentor.instrument(meter_provider=meter_provider)
        except Exception:
            logger.exception("Telemetry instrumentor failed to set up: %s", name)
            continue
        enabled.append(name)
    if enabled:
        logger.info("Telemetry instrumentors enabled: %s", ", ".join(enabled))


def initialize_telemetry() -> None:
    """Initialize telemetry components lazily to ensure fork safety in multi-process environments."""
    otel_configure_sdk()

    # To avoid importing Django before instrumenting libs
    from django.conf import settings

    # To avoid circular imports.
    from ... import __version__ as saleor_version

    instrument_libraries(settings.TELEMETRY_INSTRUMENTORS)

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
    "instrument_libraries",
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
