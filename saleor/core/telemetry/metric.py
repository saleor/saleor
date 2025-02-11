import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from threading import Lock

from django.conf import settings
from opentelemetry.util.types import Attributes, AttributeValue

from .utils import enrich_with_global_attributes, load_object

Amount = int | float


class MetricType(Enum):
    Counter = "counter"
    UpDownCounter = "up_down_counter"
    Histogram = "histogram"


class Unit(Enum):
    second = "s"
    millisecond = "ms"
    nanosecond = "ns"
    request = "{request}"


UNIT_CONVERSIONS: dict[tuple[Unit, Unit], float] = {
    (Unit.nanosecond, Unit.millisecond): 1e-6,
    (Unit.nanosecond, Unit.second): 1e-9,
}


def convert_unit(amount: Amount, unit: Unit | None, to_unit: Unit) -> Amount:
    if unit is None or unit == to_unit:
        return amount
    try:
        return amount * UNIT_CONVERSIONS[(unit, to_unit)]
    except KeyError as e:
        raise ValueError(f"Conversion from {unit} to {to_unit} not supported") from e


class Meter(ABC):
    @abstractmethod
    def create_metric(
        self,
        name: str,
        *,
        type: MetricType,
        unit: Unit,
        service: bool = False,
        description: str = "",
    ) -> None:
        pass

    def record(
        self,
        metric_name: str,
        amount: Amount,
        *,
        unit: Unit | None = None,
        attributes: Attributes = None,
    ) -> None:
        attributes = enrich_with_global_attributes(attributes)
        return self._record(metric_name, amount, unit, attributes)

    @abstractmethod
    def _record(
        self,
        metric_name: str,
        amount: Amount,
        unit: Unit | None,
        attributes: Attributes,
    ) -> None:
        pass

    @contextmanager
    def record_duration(self, metric_name: str) -> Iterator[dict[str, AttributeValue]]:
        start = time.monotonic_ns()
        attributes: dict[str, AttributeValue] = {}
        try:
            yield attributes
        finally:
            duration = time.monotonic_ns() - start
            self.record(
                metric_name, duration, unit=Unit.nanosecond, attributes=attributes
            )


def load_meter() -> type[Meter]:
    meter_cls = load_object(settings.TELEMETRY_METER_CLASS)
    if not issubclass(meter_cls, Meter):
        raise ValueError(
            "settings.TELEMETRY_METER_CLASS must point to a subclass of Meter"
        )
    return meter_cls


class MeterProxy(Meter):
    def __init__(self):
        self._meter: Meter | None = None
        self._metrics: dict[str, dict] = {}
        self._lock = Lock()

    def initialize(self, meter_cls: type[Meter]) -> None:
        if not settings.TELEMETRY_ENABLED:
            return
        if self._meter:
            raise RuntimeError("Meter already initialized")
        self._meter = meter_cls()
        for name, kwargs in self._metrics.items():
            self._meter.create_metric(name, **kwargs)

    def create_metric(self, name: str, **kwargs) -> None:
        if self._meter:
            self._meter.create_metric(name, **kwargs)
            return
        with self._lock:
            if name in self._metrics:
                raise RuntimeError(f"Metric {name} already created")
            self._metrics[name] = kwargs

    def _record(self, *args, **kwargs) -> None:
        if self._meter:
            self._meter._record(*args, **kwargs)
