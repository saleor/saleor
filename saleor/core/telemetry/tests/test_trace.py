from unittest.mock import MagicMock, patch

from opentelemetry.trace import INVALID_SPAN, Span, SpanKind

from .. import saleor_attributes, tracer
from ..trace import Tracer, TracerProxy
from ..utils import Scope


@patch("saleor.core.telemetry.trace.get_tracer")
def test_tracer_initialization(mock_get_tracer):
    # given
    instrumentation_version = "1.0.0"

    # when
    Tracer(instrumentation_version)

    # then
    assert mock_get_tracer.call_count == 2
    mock_get_tracer.assert_any_call(Scope.CORE.value, instrumentation_version, None)
    mock_get_tracer.assert_any_call(Scope.SERVICE.value, instrumentation_version, None)


@patch("saleor.core.telemetry.trace.get_tracer")
def test_tracer_start_as_current_span(mock_get_tracer):
    # given
    mock_core_tracer = MagicMock()
    mock_service_tracer = MagicMock()
    mock_span = MagicMock()
    mock_core_tracer.start_as_current_span.return_value.__enter__.return_value = (
        mock_span
    )
    mock_service_tracer.start_as_current_span.return_value.__enter__.return_value = (
        mock_span
    )

    # mock get_tracer to return different tracers for different scopes
    def mock_get_tracer_func(scope, version, provider):
        if scope == Scope.CORE.value:
            return mock_core_tracer
        return mock_service_tracer

    mock_get_tracer.side_effect = mock_get_tracer_func

    # when
    tracer = Tracer("1.0.0")

    # then
    with tracer.start_as_current_span("test_span", scope=Scope.CORE) as span:
        # verify that the core tracer was used
        mock_core_tracer.start_as_current_span.assert_called_once()
        assert span == mock_span

    with tracer.start_as_current_span("test_span", scope=Scope.SERVICE) as span:
        # verify that the service tracer was used
        mock_service_tracer.start_as_current_span.assert_called_once()
        assert span == mock_span


@patch("saleor.core.telemetry.trace.get_tracer")
def test_tracer_start_span(mock_get_tracer):
    # given
    mock_core_tracer = MagicMock()
    mock_service_tracer = MagicMock()
    mock_core_span = MagicMock()
    mock_service_span = MagicMock()
    mock_core_tracer.start_span.return_value = mock_core_span
    mock_service_tracer.start_span.return_value = mock_service_span

    # mock get_tracer to return different tracers for different scopes
    def mock_get_tracer_func(scope, version, provider):
        if scope == Scope.CORE.value:
            return mock_core_tracer
        return mock_service_tracer

    mock_get_tracer.side_effect = mock_get_tracer_func

    # when
    tracer = Tracer("1.0.0")
    core_span = tracer.start_span("test_span", scope=Scope.CORE)
    service_span = tracer.start_span("test_span", scope=Scope.SERVICE)

    # then
    mock_core_tracer.start_span.assert_called_once()
    assert core_span == mock_core_span

    mock_service_tracer.start_span.assert_called_once()
    assert service_span == mock_service_span


@patch("saleor.core.telemetry.trace.get_current_span")
def test_tracer_get_current_span(mock_get_current_span):
    # given
    mock_span = MagicMock()
    mock_get_current_span.return_value = mock_span

    # when
    tracer = Tracer("1.0.0")
    span = tracer.get_current_span()

    # then
    mock_get_current_span.assert_called_once()
    assert span == mock_span


@patch("saleor.core.telemetry.trace.logger.warning")
def test_tracer_proxy_initialize(mock_warning):
    # given
    tracer_proxy = TracerProxy()
    mock_tracer_cls = MagicMock()

    # when
    tracer_proxy.initialize(mock_tracer_cls, "1.0.0")

    # then
    mock_tracer_cls.assert_called_once_with("1.0.0")

    # initialize again should log a warning
    tracer_proxy.initialize(mock_tracer_cls, "1.0.0")
    mock_warning.assert_called_once_with("Tracer already initialized")


def test_tracer_proxy_start_as_current_span_with_tracer():
    # given
    tracer_proxy = TracerProxy()
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
    tracer_proxy._tracer = mock_tracer

    # when
    with tracer_proxy.start_as_current_span("test_span") as span:
        # then
        mock_tracer.start_as_current_span.assert_called_once_with(
            "test_span",
            scope=Scope.CORE,
            kind=SpanKind.INTERNAL,
            context=None,
            attributes=None,
            links=None,
            start_time=None,
            record_exception=True,
            set_status_on_exception=True,
            end_on_exit=True,
        )
        assert span == mock_span


def test_tracer_proxy_start_span_with_tracer():
    # given
    tracer_proxy = TracerProxy()
    mock_tracer = MagicMock(spec=Tracer)
    mock_span = MagicMock(spec=Span)
    mock_tracer.start_span.return_value = mock_span
    tracer_proxy._tracer = mock_tracer

    # when
    span = tracer_proxy.start_span("test_span")

    # then
    mock_tracer.start_span.assert_called_once_with(
        "test_span",
        scope=Scope.CORE,
        kind=SpanKind.INTERNAL,
        context=None,
        attributes=None,
        links=None,
        start_time=None,
        record_exception=True,
        set_status_on_exception=True,
    )
    assert span == mock_span


def test_tracer_proxy_get_current_span_with_tracer():
    # given
    tracer_proxy = TracerProxy()
    mock_tracer = MagicMock(spec=Tracer)
    mock_span = MagicMock(spec=Span)
    mock_tracer.get_current_span.return_value = mock_span
    tracer_proxy._tracer = mock_tracer

    # when
    span = tracer_proxy.get_current_span()

    # then
    mock_tracer.get_current_span.assert_called_once()
    assert span == mock_span


def test_tracer_proxy_start_as_current_span_without_tracer():
    # given
    tracer_proxy = TracerProxy()

    # when
    with tracer_proxy.start_as_current_span("test_span") as span:
        # then
        assert span == INVALID_SPAN


def test_tracer_proxy_start_span_without_tracer():
    # given
    tracer_proxy = TracerProxy()

    # when
    span = tracer_proxy.start_span("test_span")

    # then
    assert span == INVALID_SPAN


def test_tracer_proxy_get_current_span_without_tracer():
    # given
    tracer_proxy = TracerProxy()

    # when
    span = tracer_proxy.get_current_span()

    # then
    assert span == INVALID_SPAN


def test_span_set_attributes(get_test_spans):
    # given
    span_name = "my-span"
    key_a, val_a = "key.a", "value a"
    key_b, val_b = "key.b", "value b"

    # when
    with tracer.start_as_current_span(span_name, attributes={key_a: val_a}) as span:
        span.set_attribute(key_b, val_b)

    # then
    spans = get_test_spans()
    assert len(spans) == 1
    assert spans[0].name == span_name
    assert spans[0].attributes[key_a] == val_a
    assert spans[0].attributes[key_b] == val_b


def test_span_set_operation_name(get_test_spans):
    # given
    span_name = "my-span"

    # when
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("key", "val")

    # then
    spans = get_test_spans()
    assert len(spans) == 1
    assert spans[0].name == span_name
    assert spans[0].attributes[saleor_attributes.OPERATION_NAME] == span_name


def test_span_override_operation_name(get_test_spans):
    # given
    span_name = "my-span"
    custom_operation_name = "custom-operation"

    # when
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute(saleor_attributes.OPERATION_NAME, custom_operation_name)

    # then
    spans = get_test_spans()
    assert len(spans) == 1
    assert spans[0].name == span_name
    assert (
        spans[0].attributes[saleor_attributes.OPERATION_NAME] == custom_operation_name
    )
