import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from enum import Enum
from threading import Lock

from opentelemetry.metrics import Meter as OtelMeter
from opentelemetry.metrics import Synchronous, get_meter
from opentelemetry.util.types import Attributes, AttributeValue

from ... import __version__ as saleor_version
from .utils import (
    CORE_SCOPE,
    SERVICE_SCOPE,
    Amount,
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
    def __init__(self):
        self._core_tracer = get_meter(CORE_SCOPE, saleor_version)
        self._service_tracer = get_meter(SERVICE_SCOPE, saleor_version)
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
        service_scope: bool = False,
        description: str = "",
    ) -> None:
        meter = self._service_tracer if service_scope else self._core_tracer
        with self._lock:
            if name in self._instruments:
                raise DuplicateMetricError(name)
            instrument = self._create_instrument(meter, name, type, unit, description)
            self._instruments[name] = unit, instrument

    def record(
        self,
        metric_name: str,
        amount: Amount,
        *,
        unit: Unit | None = None,
        attributes: Attributes = None,
    ) -> None:
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
    def __init__(self):
        self._meter: Meter | None = None
        self._metrics: dict[str, dict] = {}
        self._lock = Lock()

    def initialize(self, meter_cls: type[Meter]) -> None:
        if self._meter:
            logger.warning("Tracer already initialized")
        self._meter = meter_cls()
        with self._lock:
            for name, kwargs in self._metrics.items():
                self._meter.create_metric(name, **kwargs)

    def create_metric(
        self,
        name: str,
        *,
        type: MetricType,
        unit: Unit,
        service_scope: bool = False,
        description: str = "",
    ) -> None:
        kwargs = {
            "type": type,
            "unit": unit,
            "service_scope": service_scope,
            "description": description,
        }
        if self._meter:
            self._meter.create_metric(
                name,
                type=type,
                unit=unit,
                service_scope=service_scope,
                description=description,
            )
        else:
            with self._lock:
                if name in self._metrics:
                    raise DuplicateMetricError(name)
                self._metrics[name] = kwargs

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
