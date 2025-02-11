from collections.abc import Callable, Iterator
from contextlib import contextmanager
from threading import Lock

from opentelemetry.metrics import Meter as OtelMeter
from opentelemetry.metrics import Synchronous, get_meter
from opentelemetry.trace import get_current_span, get_tracer

from ... import __version__ as saleor_version
from .metric import Amount, Meter, MetricType, Unit, convert_unit
from .trace import Attributes, Span, SpanConfig, Tracer

SYSTEM_SCOPE = "saleor.system"
SERVICE_SCOPE = "saleor.service"


class OpenTelemetryTracer(Tracer):
    def __init__(self):
        self._system_tracer = get_tracer(SYSTEM_SCOPE, saleor_version)
        self._service_tracer = get_tracer(SERVICE_SCOPE, saleor_version)

    @contextmanager
    def _start_as_current_span(
        self, name: str, service: bool, span_config: SpanConfig, end_on_exit: bool
    ) -> Iterator[Span]:
        tracer = self._service_tracer if service else self._system_tracer
        with tracer.start_as_current_span(
            name, **span_config, end_on_exit=end_on_exit
        ) as span:
            yield span

    def _start_span(self, name: str, service: bool, span_config: SpanConfig) -> Span:
        tracer = self._service_tracer if service else self._system_tracer
        return tracer.start_span(name, **span_config)

    def get_current_span(self) -> Span:
        return get_current_span()


def get_instrument_method(
    instrument: Synchronous,
) -> Callable[[Amount, Attributes], None]:
    if hasattr(instrument, "record"):
        return instrument.record
    return getattr(instrument, "add")


class OpenTelemetryMeter(Meter):
    def __init__(self):
        self._system_tracer = get_meter(SYSTEM_SCOPE, saleor_version)
        self._service_tracer = get_meter(SERVICE_SCOPE, saleor_version)
        self._instruments: dict[str, tuple[Unit, Synchronous]] = {}
        self._lock = Lock()

    @staticmethod
    def _create_instrument(
        otel_meter: OtelMeter,
        name: str,
        type: MetricType,
        unit: str,
        description: str,
    ) -> Synchronous:
        kwargs = {"unit": unit, "description": description}
        if type == MetricType.Counter:
            return otel_meter.create_counter(name, **kwargs)
        if type == MetricType.UpDownCounter:
            return otel_meter.create_up_down_counter(name, **kwargs)
        if type == MetricType.Histogram:
            return otel_meter.create_histogram(name, **kwargs)
        raise AttributeError(f"Unsupported instrument type: {type}")

    def create_metric(
        self,
        name: str,
        *,
        type: MetricType,
        unit: Unit,
        service: bool = False,
        description: str = "",
    ) -> None:
        meter = self._service_tracer if service else self._system_tracer
        with self._lock:
            if name in self._instruments:
                raise RuntimeError(f"Metric {name} already created")
            instrument = self._create_instrument(
                meter, name, type, unit.value, description
            )
            self._instruments[name] = unit, instrument

    def _record(
        self,
        metric_name: str,
        amount: Amount,
        unit: Unit | None,
        attributes: Attributes,
    ) -> None:
        if metric_name not in self._instruments:
            raise RuntimeError(f"Metric {metric_name} must be created first")
        instrument_unit, instrument = self._instruments[metric_name]
        amount = convert_unit(amount, unit, instrument_unit)
        return get_instrument_method(instrument)(amount, attributes)
