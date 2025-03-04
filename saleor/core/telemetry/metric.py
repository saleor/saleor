import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from enum import Enum
from threading import Lock

from opentelemetry.metrics import Meter as OtelMeter
from opentelemetry.metrics import Synchronous, get_meter
from opentelemetry.util.types import Attributes, AttributeValue

from .utils import (
    Amount,
    Scope,
    Unit,
    convert_unit,
    enrich_with_global_attributes,
)

logger = logging.getLogger(__name__)


class DuplicateMetricError(RuntimeError):
    def __init__(self, name):
        super().__init__(f"Metric {name} already created")


class MetricType(Enum):
    COUNTER = "counter"
    UP_DOWN_COUNTER = "up_down_counter"
    HISTOGRAM = "histogram"


def get_instrument_method(
    instrument: Synchronous,
) -> Callable[[Amount, Attributes], None]:
    if hasattr(instrument, "record"):
        return instrument.record
    return getattr(instrument, "add")


class Meter:
    """Interface for instrumenting code with metrics collection.

    The class provides an interface for creating and recording metrics.
    This default implementation uses OpenTelemetry to provide that but can be easily
    subclassed to alter or change the telemetry implementation.

    The Meter operates with two distinct scopes:
        - CORE: For internal system operations and core functionality
        - SERVICE: For business logic and service-level operations

    Note:
        The Meter internally uses the global OpenTelemetry MeterProvider, which should
        be initialized following OpenTelemetry's standard process, for example using
        the `opentelemetry-instrument` tool.

    """

    def __init__(self, instrumentation_version: str):
        self._core_tracer = get_meter(Scope.CORE.value, instrumentation_version)
        self._service_tracer = get_meter(Scope.SERVICE.value, instrumentation_version)
        self._instruments: dict[str, tuple[Unit, Synchronous]] = {}
        self._lock = Lock()

    @staticmethod
    def _create_instrument(
        otel_meter: OtelMeter,
        name: str,
        type: MetricType,
        unit: Unit,
        description: str,
    ) -> Synchronous:
        kwargs = {"unit": unit.value, "description": description}
        if type == MetricType.COUNTER:
            return otel_meter.create_counter(name, **kwargs)
        if type == MetricType.UP_DOWN_COUNTER:
            return otel_meter.create_up_down_counter(name, **kwargs)
        if type == MetricType.HISTOGRAM:
            return otel_meter.create_histogram(name, **kwargs)
        raise AttributeError(f"Unsupported instrument type: {type}")

    def create_metric(
        self,
        name: str,
        *,
        type: MetricType,
        unit: Unit,
        scope: Scope = Scope.CORE,
        description: str = "",
    ) -> str:
        """Create a new metric with specified parameters.

        Args:
            name: The name of the metric
            type: Type of the metric
            unit: Unit of the metric
            scope: The scope of the metric, defaults to Scope.CORE
            description: Optional description of the metric

        Returns:
            str: The name of the created metric

        """
        meter = self._service_tracer if scope.is_service else self._core_tracer
        with self._lock:
            if name in self._instruments:
                raise DuplicateMetricError(name)
            instrument = self._create_instrument(meter, name, type, unit, description)
            self._instruments[name] = unit, instrument
        return name

    def record(
        self,
        metric_name: str,
        amount: Amount,
        *,
        unit: Unit | None = None,
        attributes: Attributes = None,
    ) -> None:
        """Record a measurement for the specified metric.

        Args:
            metric_name: Name of the metric to record a measurement
            amount: Value to record
            unit: Optional unit of the measurement (converted if different from metric unit)
            attributes: Attributes to record with the measurement

        """
        attributes = enrich_with_global_attributes(attributes)
        if metric_name not in self._instruments:
            raise RuntimeError(f"Metric {metric_name} must be created first")
        instrument_unit, instrument = self._instruments[metric_name]
        amount = convert_unit(amount, unit, instrument_unit)
        return get_instrument_method(instrument)(amount, attributes)

    @contextmanager
    def record_duration(self, metric_name: str) -> Iterator[dict[str, AttributeValue]]:
        start = time.monotonic_ns()
        attributes: dict[str, AttributeValue] = {}
        try:
            yield attributes
        finally:
            duration = time.monotonic_ns() - start
            self.record(
                metric_name, duration, unit=Unit.NANOSECOND, attributes=attributes
            )


class MeterProxy(Meter):
    """A proxy that enables delayed initialization of Meter.

    This class is designed to ensure fork safety in multi-process environments by
    allowing Meter initialization to be deferred until after process forking.
    """

    def __init__(self):
        self._meter: Meter | None = None
        self._metrics: dict[str, dict] = {}
        self._lock = Lock()

    def initialize(self, meter_cls: type[Meter], instrumentation_version: str) -> None:
        if self._meter:
            logger.warning("Tracer already initialized")
        self._meter = meter_cls(instrumentation_version)
        with self._lock:
            for name, kwargs in self._metrics.items():
                self._meter.create_metric(name, **kwargs)

    def create_metric(
        self,
        name: str,
        *,
        type: MetricType,
        unit: Unit,
        scope: Scope = Scope.CORE,
        description: str = "",
    ) -> str:
        kwargs = {
            "type": type,
            "unit": unit,
            "scope": scope,
            "description": description,
        }
        if self._meter:
            return self._meter.create_metric(
                name,
                type=type,
                unit=unit,
                scope=scope,
                description=description,
            )
        with self._lock:
            if name in self._metrics:
                raise DuplicateMetricError(name)
            self._metrics[name] = kwargs
        return name

    def record(
        self,
        metric_name: str,
        amount: Amount,
        *,
        unit: Unit | None = None,
        attributes: Attributes = None,
    ) -> None:
        if self._meter:
            self._meter.record(metric_name, amount, unit=unit, attributes=attributes)
