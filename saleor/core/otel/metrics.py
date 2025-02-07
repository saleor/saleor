import time
from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum

from opentelemetry.metrics import Counter, Histogram, UpDownCounter, get_meter
from opentelemetry.util.types import Attributes, AttributeValue

from .context import enrich_with_trace_attributes

OTEL_INSTRUMENT_TYPE = Counter | Histogram | UpDownCounter


class MetricType(Enum):
    Counter = "counter"
    UpDownCounter = "up_down_counter"
    Histogram = "histogram"


class Metric:
    def __init__(
        self,
        type: MetricType,
        instrument: OTEL_INSTRUMENT_TYPE,
    ):
        self._instrument = instrument
        self.type = type

    def record(self, amount: int | float, attributes: Attributes = None) -> None:
        if isinstance(self._instrument, Histogram):
            return self._instrument.record(amount, attributes)
        return self._instrument.add(amount, attributes)


class Meter:
    def __init__(self, internal_scope: str, public_scope: str, version: str):
        self._internal_meter = get_meter(internal_scope, version)
        self._public_meter = get_meter(public_scope, version)
        self._instruments: dict[str, Metric] = {}

    def _create_instrument(
        self, name: str, type: MetricType, internal: bool, unit: str, description: str
    ) -> Metric:
        meter = self._internal_meter if internal else self._public_meter
        instrument: OTEL_INSTRUMENT_TYPE | None = None
        if type == MetricType.Counter:
            instrument = meter.create_counter(name, unit=unit, description=description)
        elif type == MetricType.UpDownCounter:
            instrument = meter.create_up_down_counter(
                name, unit=unit, description=description
            )
        elif type == MetricType.Histogram:
            instrument = meter.create_histogram(
                name, unit=unit, description=description
            )
        if instrument is None:
            raise AttributeError(f"Unsupported instrument type: {type}")
        return Metric(type, instrument)

    def create_metric(
        self,
        name: str,
        type: MetricType,
        internal: bool,
        *,
        unit: str = "",
        description: str = "",
    ):
        if name in self._instruments:
            raise RuntimeError(f"Instrument {name} already exists")
        instrument = self._create_instrument(
            name, type, internal, unit=unit, description=description
        )
        self._instruments[name] = instrument

    def _get_instrument(self, name: str) -> Metric:
        try:
            return self._instruments[name]
        except KeyError as e:
            raise RuntimeError(f"Instrument {name} was not created") from e

    def record(
        self, metric_name: str, amount: int | float, attributes: Attributes = None
    ) -> None:
        attributes = enrich_with_trace_attributes(attributes)
        return self._get_instrument(metric_name).record(amount, attributes)

    @contextmanager
    def record_duration_ms(
        self, metric_name: str
    ) -> Generator[dict[str, AttributeValue], None, None]:
        start = time.monotonic_ns()
        attributes: dict[str, AttributeValue] = {}
        try:
            yield attributes
        finally:
            duration_ms = (time.monotonic_ns() - start) / 1_000_000
            self._get_instrument(metric_name).record(duration_ms, attributes=attributes)
