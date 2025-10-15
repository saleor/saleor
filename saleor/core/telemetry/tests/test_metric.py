from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.metrics import Synchronous
from opentelemetry.sdk.metrics.export import HistogramDataPoint

from ....tests.utils import get_metric_data
from .. import meter
from ..metric import (
    DuplicateMetricError,
    Meter,
    MeterProxy,
    MetricType,
    get_instrument_method,
)
from ..utils import Scope, Unit


def test_get_instrument_method_add():
    # given
    instrument = MagicMock(spec=Synchronous)
    instrument.add = MagicMock()

    # when
    method = get_instrument_method(instrument)

    # then
    assert method == instrument.add


def test_get_instrument_method_record():
    # given
    instrument = MagicMock(spec=Synchronous)
    instrument.record = MagicMock()

    # when
    method = get_instrument_method(instrument)

    # then
    assert method == instrument.record


@patch("saleor.core.telemetry.metric.get_meter")
def test_meter_initialization(mock_get_meter):
    # given
    instrumentation_version = "1.0.0"

    # when
    Meter(instrumentation_version)

    # then
    assert mock_get_meter.call_count == 2
    mock_get_meter.assert_any_call(Scope.CORE.value, instrumentation_version, None)
    mock_get_meter.assert_any_call(Scope.SERVICE.value, instrumentation_version, None)


def test_meter_create_counter():
    # given
    mock_otel_meter = MagicMock()
    mock_counter = MagicMock()
    mock_otel_meter.create_counter.return_value = mock_counter

    # when
    instrument = Meter._create_instrument(
        mock_otel_meter,
        "counter_metric",
        MetricType.COUNTER,
        Unit.REQUEST,
        "Counter description",
    )

    # then
    mock_otel_meter.create_counter.assert_called_once_with(
        "counter_metric", Unit.REQUEST.value, "Counter description"
    )
    assert instrument == mock_counter


def test_meter_create_up_down_counter():
    # given
    mock_otel_meter = MagicMock()
    mock_updown_counter = MagicMock()
    mock_otel_meter.create_up_down_counter.return_value = mock_updown_counter

    # when
    instrument = Meter._create_instrument(
        mock_otel_meter,
        "updown_counter_metric",
        MetricType.UP_DOWN_COUNTER,
        Unit.REQUEST,
        "UpDownCounter description",
    )

    # then
    mock_otel_meter.create_up_down_counter.assert_called_once_with(
        "updown_counter_metric", Unit.REQUEST.value, "UpDownCounter description"
    )
    assert instrument == mock_updown_counter


def test_meter_create_histogram():
    # given
    mock_otel_meter = MagicMock()
    mock_histogram = MagicMock()
    mock_otel_meter.create_histogram.return_value = mock_histogram

    # when
    instrument = Meter._create_instrument(
        mock_otel_meter,
        "histogram_metric",
        MetricType.HISTOGRAM,
        Unit.SECOND,
        "Histogram description",
    )

    # then
    mock_otel_meter.create_histogram.assert_called_once_with(
        "histogram_metric",
        Unit.SECOND.value,
        "Histogram description",
        explicit_bucket_boundaries_advisory=None,
    )
    assert instrument == mock_histogram


def test_meter_create_unsupported_metric_type():
    mock_otel_meter = MagicMock()
    with pytest.raises(AttributeError, match="Unsupported instrument type"):
        Meter._create_instrument(
            mock_otel_meter,
            "invalid_metric",
            "INVALID_TYPE",  # type: ignore[arg-type]
            Unit.REQUEST,
            "Invalid description",
        )


def test_meter_create_core_metric():
    # given
    meter = Meter("1.0.0")

    with patch.object(meter, "_create_instrument") as mock_create_instrument:
        mock_instrument = MagicMock()
        mock_create_instrument.return_value = mock_instrument

        # when
        metric_name = meter.create_metric(
            "core_metric",
            type=MetricType.COUNTER,
            unit=Unit.REQUEST,
            scope=Scope.CORE,
            description="Core metric description",
        )

        # then
        mock_create_instrument.assert_called_once()
        assert metric_name == "core_metric"
        assert "core_metric" in meter._instruments
        assert meter._instruments["core_metric"] == (Unit.REQUEST, mock_instrument)


def test_meter_create_service_metric():
    # given
    meter = Meter("1.0.0")

    with patch.object(meter, "_create_instrument") as mock_create_instrument:
        mock_instrument = MagicMock()
        mock_create_instrument.return_value = mock_instrument

        # when
        metric_name = meter.create_metric(
            "service_metric",
            type=MetricType.HISTOGRAM,
            unit=Unit.SECOND,
            scope=Scope.SERVICE,
            description="Service metric description",
        )

        # then
        mock_create_instrument.assert_called_once()
        assert metric_name == "service_metric"
        assert "service_metric" in meter._instruments
        assert meter._instruments["service_metric"] == (Unit.SECOND, mock_instrument)


def test_create_duplicate_metric():
    # given
    meter = Meter("1.0.0")
    meter._instruments["service_metric"] = (Unit.REQUEST, MagicMock())

    with patch.object(meter, "_create_instrument") as mock_create_instrument:
        mock_instrument = MagicMock()
        mock_create_instrument.return_value = mock_instrument

        # Test duplicate metric
        with pytest.raises(DuplicateMetricError, match="Metric .* already created"):
            meter.create_metric(
                "service_metric",
                type=MetricType.COUNTER,
                unit=Unit.REQUEST,
                scope=Scope.SERVICE,
            )


def test_meter_record():
    # given
    meter = Meter("1.0.0")
    mock_instrument = MagicMock(spec=Synchronous)
    mock_instrument.add = MagicMock()
    meter._instruments["test_metric"] = (Unit.REQUEST, mock_instrument)

    # when
    meter.record(
        "test_metric",
        1,
        Unit.REQUEST,
        attributes={"attr1": "value1"},
    )

    # Verify that add was called with the correct arguments
    mock_instrument.add.assert_called_once_with(1, {"attr1": "value1"})


@patch("saleor.core.telemetry.metric.convert_unit")
def test_meter_record_with_different_unit(mock_convert_unit):
    # given
    meter = Meter("1.0.0")
    mock_instrument = MagicMock(spec=Synchronous)
    mock_instrument.add = MagicMock()
    meter._instruments["test_metric"] = (Unit.REQUEST, mock_instrument)

    mock_convert_unit.return_value = 1000

    # when
    meter.record(
        "test_metric",
        1,
        unit=Unit.SECOND,
        attributes={"attr1": "value1"},
    )

    # then
    mock_convert_unit.assert_called_once_with(1, Unit.SECOND, Unit.REQUEST)
    mock_instrument.add.assert_called_with(1000, {"attr1": "value1"})


def test_meter_record_non_existent_metric():
    meter = Meter("1.0.0")
    with pytest.raises(RuntimeError, match="Metric .* must be created first"):
        meter.record(
            "non_existent_metric",
            1,
            Unit.REQUEST,
        )


@patch("time.monotonic_ns")
def test_meter_record_duration(mock_monotonic_ns):
    # given
    meter = Meter("1.0.0")
    mock_monotonic_ns.side_effect = [1000000, 2000000]  # 1ms difference
    mock_instrument = MagicMock(spec=Synchronous)
    mock_instrument.record = MagicMock()
    meter._instruments["test_metric"] = (Unit.NANOSECOND, mock_instrument)

    # when
    with meter.record_duration("test_metric") as attrs:
        attrs["attr1"] = "value1"

    # then
    mock_instrument.record.assert_called_once_with(1000000, {"attr1": "value1"})


def test_meter_proxy_initialize():
    # given
    meter_proxy = MeterProxy()
    mock_meter_cls = MagicMock(spec=Meter)
    mock_meter = MagicMock(spec=Meter)
    mock_meter_cls.return_value = mock_meter

    meter_proxy.create_metric(
        "test_metric",
        type=MetricType.COUNTER,
        unit=Unit.REQUEST,
        scope=Scope.CORE,
        description="Test metric description",
    )

    # when
    meter_proxy.initialize(mock_meter_cls, "1.0.0")

    # then
    mock_meter_cls.assert_called_once_with("1.0.0")
    assert meter_proxy._meter == mock_meter

    mock_meter.create_metric.assert_called_once_with(
        "test_metric",
        type=MetricType.COUNTER,
        unit=Unit.REQUEST,
        scope=Scope.CORE,
        description="Test metric description",
        bucket_boundaries=None,
    )

    # Initialize again should log a warning
    with patch("saleor.core.telemetry.metric.logger.warning") as mock_warning:
        meter_proxy.initialize(mock_meter_cls, "1.0.0")
        mock_warning.assert_called_once_with("Meter already initialized")


def test_meter_proxy_create_metric_without_meter():
    # given
    meter_proxy = MeterProxy()

    # when
    metric_name = meter_proxy.create_metric(
        "test_metric",
        type=MetricType.COUNTER,
        unit=Unit.REQUEST,
        scope=Scope.CORE,
        description="Test metric description",
    )

    # Verify that the metric was added to the proxy
    assert metric_name == "test_metric"
    assert "test_metric" in meter_proxy._metrics
    assert meter_proxy._metrics["test_metric"]["type"] == MetricType.COUNTER
    assert meter_proxy._metrics["test_metric"]["unit"] == Unit.REQUEST
    assert meter_proxy._metrics["test_metric"]["scope"] == Scope.CORE
    assert (
        meter_proxy._metrics["test_metric"]["description"] == "Test metric description"
    )


def test_meter_proxy_create_duplicate_metric_without_meter():
    # given
    meter_proxy = MeterProxy()
    meter_proxy.create_metric(
        "test_metric",
        type=MetricType.COUNTER,
        unit=Unit.REQUEST,
        scope=Scope.CORE,
        description="Test metric description",
    )

    # then
    with pytest.raises(DuplicateMetricError, match="Metric .* already created"):
        meter_proxy.create_metric(
            "test_metric",
            type=MetricType.COUNTER,
            unit=Unit.REQUEST,
            scope=Scope.CORE,
        )


def test_meter_proxy_create_metric_with_meter():
    # given
    meter_proxy = MeterProxy()
    mock_meter = MagicMock(spec=Meter)
    mock_meter.create_metric.return_value = "test_metric"
    meter_proxy._meter = mock_meter

    # when
    metric_name = meter_proxy.create_metric(
        "test_metric",
        type=MetricType.COUNTER,
        unit=Unit.REQUEST,
        scope=Scope.CORE,
        description="Test metric description",
    )

    # then
    mock_meter.create_metric.assert_called_once_with(
        "test_metric",
        type=MetricType.COUNTER,
        unit=Unit.REQUEST,
        scope=Scope.CORE,
        description="Test metric description",
        bucket_boundaries=None,
    )
    assert metric_name == "test_metric"


def test_meter_proxy_record_with_meter():
    # given
    meter_proxy = MeterProxy()
    mock_meter = MagicMock(spec=Meter)
    meter_proxy._meter = mock_meter

    # when
    meter_proxy.record(
        "test_metric",
        1,
        unit=Unit.REQUEST,
        attributes={"attr1": "value1"},
    )

    # then
    mock_meter.record.assert_called_once_with(
        "test_metric",
        1,
        unit=Unit.REQUEST,
        attributes={"attr1": "value1"},
    )


def test_meter_create_histogram_with_explicit_bucket_boundaries(get_test_metrics_data):
    # given
    name = "test_histogram_metric"
    unit = Unit.SECOND
    description = "Test histogram metric description"
    attributes = {"attr1": "value1"}
    bucket_boundaries = (0.1, 0.25, 0.5, 1, 10)
    meter.create_metric(
        name,
        type=MetricType.HISTOGRAM,
        unit=unit,
        description=description,
        bucket_boundaries=bucket_boundaries,
    )

    # when
    # Record values at each bucket boundary to validate bucket assignment
    # Each value should fall into different buckets based on boundary definitions
    meter.record(name, 0.1, unit=Unit.SECOND, attributes=attributes)
    meter.record(name, 0.25, unit=Unit.SECOND, attributes=attributes)
    meter.record(name, 0.5, unit=Unit.SECOND, attributes=attributes)
    meter.record(name, 1, unit=Unit.SECOND, attributes=attributes)
    meter.record(name, 10, unit=Unit.SECOND, attributes=attributes)
    # Record a value outside the defined buckets to verify overflow handling
    meter.record(name, 20, unit=Unit.SECOND, attributes=attributes)

    # then
    metric_data = get_metric_data(get_test_metrics_data(), name, scope=Scope.CORE)
    assert metric_data.name == name
    assert metric_data.unit == unit.value
    assert metric_data.description == description
    data_point = metric_data.data.data_points[0]
    assert isinstance(data_point, HistogramDataPoint)
    assert data_point.attributes == attributes
    assert data_point.explicit_bounds == bucket_boundaries
    assert data_point.count == 6  # Total number of recorded values
    assert data_point.bucket_counts == (1, 1, 1, 1, 1, 1)  # One value in each bucket
    assert data_point.min == 0.1  # Smallest recorded value
    assert data_point.max == 20  # Largest recorded value
    assert data_point.sum == 31.85  # Sum of all recorded values
