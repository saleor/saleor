import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from threading import Lock

from opentelemetry.util.types import Attributes, AttributeValue

from .utils import Amount, Unit, enrich_with_global_attributes

logger = logging.getLogger(__name__)


class DuplicateMetricError(RuntimeError):
    def __init__(self, name):
        super().__init__(f"Metric {name} already created")


class MetricType(Enum):
    COUNTER = "counter"
    UP_DOWN_COUNTER = "up_down_counter"
    HISTOGRAM = "histogram"


class Meter(ABC):
    def create_metric(
        self,
        name: str,
        *,
        type: MetricType,
        unit: Unit,
        service_scope: bool = False,
        description: str = "",
    ) -> None:
        return self._create_metric(name, type, unit, service_scope, description)

    @abstractmethod
    def _create_metric(
        self,
        name: str,
        type: MetricType,
        unit: Unit,
        service_scope: bool,
        description: str,
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
                metric_name, duration, unit=Unit.NANOSECOND, attributes=attributes
            )


class MeterProxy(Meter):
    def __init__(self):
        self._meter: Meter | None = None
        self._metrics: dict[str, tuple[tuple, dict]] = {}
        self._lock = Lock()

    def initialize(self, meter_cls: type[Meter]) -> None:
        if self._meter:
            logger.warning("Tracer already initialized")
        self._meter = meter_cls()
        with self._lock:
            for name, (args, kwargs) in self._metrics.items():
                self._meter._create_metric(name, *args, **kwargs)

    def _create_metric(self, name: str, *args, **kwargs) -> None:
        if self._meter:
            self._meter._create_metric(name, *args, **kwargs)
        else:
            with self._lock:
                if name in self._metrics:
                    raise DuplicateMetricError(name)
                self._metrics[name] = args, kwargs

    def _record(self, *args, **kwargs) -> None:
        if self._meter:
            self._meter._record(*args, **kwargs)
