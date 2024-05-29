from unittest.mock import patch

from django.test import override_settings

from ..public_log_drain import LogDrainAttributes, LogLevel, LogType
from ..tasks import emit_public_log_task


@override_settings(OTEL_TRANSPORTED_ENDPOINT=None, HTTP_TRANSPORTED_ENDPOINT=None)
@patch("saleor.public_log_drain.tasks.PublicLogDrain.emit_log")
def test_emit_public_log_no_transporters(mocked_emit_log):
    # given
    logger_name = "test_name"
    trace_id = 1
    span_id = 1
    attributes = LogDrainAttributes(
        type=LogType.WEBHOOK_SENT.name,
        level=LogLevel.INFO.name,
        message="Test message",
        version="1",
        checkout_id=None,
        order_id=None,
    )
    # when
    emit_public_log_task.delay(logger_name, trace_id, span_id, attributes.__dict__)
    # then
    mocked_emit_log.assert_not_called()


@override_settings(
    OTEL_TRANSPORTED_ENDPOINT="test-endpoint", HTTP_TRANSPORTED_ENDPOINT=None
)
@patch("saleor.public_log_drain.tasks.PublicLogDrain.emit_log")
def test_emit_public_log_otel(mocked_emit_log):
    # given
    logger_name = "test_name"
    trace_id = 1
    span_id = 1
    attributes = LogDrainAttributes(
        type=LogType.WEBHOOK_SENT.name,
        level=LogLevel.INFO.name,
        message="Test message",
        version="1",
        checkout_id=None,
        order_id=None,
    )
    # when
    emit_public_log_task.delay(logger_name, trace_id, span_id, attributes.__dict__)
    # then
    mocked_emit_log.assert_called_once_with(logger_name, trace_id, span_id, attributes)


@override_settings(
    HTTP_TRANSPORTED_ENDPOINT="test-endpoint", OTEL_TRANSPORTED_ENDPOINT=None
)
@patch("saleor.public_log_drain.tasks.PublicLogDrain.emit_log")
def test_emit_public_log_http(mocked_emit_log):
    # given
    logger_name = "test_name"
    trace_id = 1
    span_id = 1
    attributes = LogDrainAttributes(
        type=LogType.WEBHOOK_SENT.name,
        level=LogLevel.INFO.name,
        message="Test message",
        version="1",
        checkout_id=None,
        order_id=None,
    )
    # when
    emit_public_log_task.delay(logger_name, trace_id, span_id, attributes.__dict__)
    # then
    mocked_emit_log.assert_called_once_with(logger_name, trace_id, span_id, attributes)


@override_settings(
    HTTP_TRANSPORTED_ENDPOINT="test-endpoint-http",
    OTEL_TRANSPORTED_ENDPOINT="test-endpoint-otel",
)
@patch("saleor.public_log_drain.tasks.PublicLogDrain.emit_log")
def test_emit_public_log_otel_and_http(mocked_emit_log):
    # given
    logger_name = "test_name"
    trace_id = 1
    span_id = 1
    attributes = LogDrainAttributes(
        type=LogType.WEBHOOK_SENT.name,
        level=LogLevel.INFO.name,
        message="Test message",
        version="1",
        checkout_id=None,
        order_id=None,
    )
    # when
    emit_public_log_task(logger_name, trace_id, span_id, attributes.__dict__)
    # then
    mocked_emit_log.assert_called_once_with(logger_name, trace_id, span_id, attributes)
