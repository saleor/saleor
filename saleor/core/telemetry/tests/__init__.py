from collections.abc import Mapping

from opentelemetry.sdk.metrics import (
    Counter,
    Histogram,
    MeterProvider,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality,
    InMemoryMetricReader,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ..metric import Meter
from ..trace import Tracer

DELTA_TEMPORALITY = {
    Counter: AggregationTemporality.DELTA,
    UpDownCounter: AggregationTemporality.CUMULATIVE,
    Histogram: AggregationTemporality.DELTA,
    ObservableCounter: AggregationTemporality.DELTA,
    ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
    ObservableGauge: AggregationTemporality.CUMULATIVE,
}


class TestTracer(Tracer):
    tracer_provider = TracerProvider()
    span_exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    _inject_context = False

    def inject_context(self, carrier: Mapping[str, str | list[str]]):
        if self._inject_context:
            super().inject_context(carrier)


class TestMeter(Meter):
    metric_reader = InMemoryMetricReader(preferred_temporality=DELTA_TEMPORALITY)
    meter_provider = MeterProvider((metric_reader,))
