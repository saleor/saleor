from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.trace import StatusCode

from .....core.models import EventDeliveryStatus
from .....core.telemetry import set_global_attributes
from .....tests.utils import get_metric_data_point
from ...metrics import (
    METRIC_EXTERNAL_REQUEST_BODY_SIZE,
    METRIC_EXTERNAL_REQUEST_COUNT,
    METRIC_EXTERNAL_REQUEST_DURATION,
)
from ...utils import WebhookResponse
from ..transport import _send_webhook_request_sync


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_using_http")
@patch("saleor.webhook.transport.synchronous.transport.webhooks_otel_trace")
@patch("saleor.webhook.transport.synchronous.transport.attempt_update")
def test_send_webhook_request_sync_set_span_status_failed_invalid_json(
    mock_attempt_update,
    mock_webhooks_otel_trace,
    mock_send_webhook_using_http,
    event_delivery_payload_in_database,
):
    # given
    mock_span = MagicMock()
    mock_webhooks_otel_trace.return_value.__enter__.return_value = mock_span

    mock_response = MagicMock(spec=WebhookResponse)
    mock_response.response_status_code = 200
    mock_response.status = EventDeliveryStatus.SUCCESS
    mock_response.content = ""  # Simulating invalid JSON
    mock_response.duration = 2.0
    mock_send_webhook_using_http.return_value = mock_response

    # when
    _send_webhook_request_sync(event_delivery_payload_in_database)

    # then
    mock_span.set_status.assert_called_once_with(
        StatusCode.ERROR,
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_using_http")
@patch("saleor.webhook.transport.synchronous.transport.webhooks_otel_trace")
@patch("saleor.webhook.transport.synchronous.transport.attempt_update")
def test_send_webhook_request_sync_set_span_status_failed_error_response(
    mock_attempt_update,
    mock_webhooks_otel_trace,
    mock_send_webhook_using_http,
    event_delivery_payload_in_database,
):
    # given
    mock_span = MagicMock()
    mock_webhooks_otel_trace.return_value.__enter__.return_value = mock_span

    mock_response = MagicMock(spec=WebhookResponse)
    mock_response.response_status_code = 500
    mock_response.status = EventDeliveryStatus.FAILED
    mock_response.content = "{}"
    mock_response.duration = 2.0
    mock_send_webhook_using_http.return_value = mock_response

    # when
    _send_webhook_request_sync(event_delivery_payload_in_database)

    # then
    mock_span.set_status.assert_called_once_with(
        StatusCode.ERROR,
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_using_http")
def test_send_webhook_request_sync_record_external_request(
    mock_send_webhook_using_http,
    webhook_response,
    event_delivery_payload_in_database,
    get_test_metrics_data,
):
    # given
    webhook_response.content = "{}"
    mock_send_webhook_using_http.return_value = webhook_response
    payload_size = len(
        event_delivery_payload_in_database.payload.get_payload().encode("utf-8")
    )
    global_attributes = {"global.attr": "value"}

    # when
    with set_global_attributes(global_attributes):
        _send_webhook_request_sync(event_delivery_payload_in_database)

    # then
    attributes = {
        "server.address": "www.example.com",
        "saleor.app.identifier": event_delivery_payload_in_database.webhook.app.identifier,
        "saleor.webhook.event_type": event_delivery_payload_in_database.event_type,
        "saleor.webhook.execution_mode": "sync",
        **global_attributes,
    }
    metrics_data = get_test_metrics_data()
    external_request_count = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_COUNT
    )
    assert external_request_count.value == 1
    assert external_request_count.attributes == attributes

    external_request_duration = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_DURATION
    )
    assert external_request_duration.attributes == attributes
    assert external_request_duration.count == 1
    assert external_request_duration.sum == webhook_response.duration

    external_request_content_length = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_BODY_SIZE
    )
    assert external_request_content_length.attributes == attributes
    assert external_request_content_length.count == 1
    assert external_request_content_length.sum == payload_size


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_using_http")
def test_send_webhook_request_sync_record_external_request_when_delivery_attempt_failed(
    mock_send_webhook_using_http,
    webhook_response_failed,
    event_delivery_payload_in_database,
    get_test_metrics_data,
):
    # given
    webhook_response_failed.content = "{}"
    mock_send_webhook_using_http.return_value = webhook_response_failed
    payload_size = len(
        event_delivery_payload_in_database.payload.get_payload().encode("utf-8")
    )
    global_attributes = {"global.attr": "value"}

    # when
    with set_global_attributes(global_attributes):
        _send_webhook_request_sync(event_delivery_payload_in_database)

    # then
    attributes = {
        "server.address": "www.example.com",
        "error.type": "request_error",
        "saleor.app.identifier": event_delivery_payload_in_database.webhook.app.identifier,
        "saleor.webhook.event_type": event_delivery_payload_in_database.event_type,
        "saleor.webhook.execution_mode": "sync",
        **global_attributes,
    }
    metrics_data = get_test_metrics_data()
    external_request_count = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_COUNT
    )
    assert external_request_count.value == 1
    assert external_request_count.attributes == attributes

    external_request_duration = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_DURATION
    )
    assert external_request_duration.attributes == attributes
    assert external_request_duration.count == 1
    assert external_request_duration.sum == webhook_response_failed.duration

    external_request_content_length = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_BODY_SIZE
    )
    assert external_request_content_length.attributes == attributes
    assert external_request_content_length.count == 1
    assert external_request_content_length.sum == payload_size


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_using_http")
def test_send_webhook_request_sync_record_external_request_with_invalid_json_response(
    mock_send_webhook_using_http,
    webhook_response,
    event_delivery_payload_in_database,
    get_test_metrics_data,
):
    # given
    webhook_response.content = "Invalid JSON"
    mock_send_webhook_using_http.return_value = webhook_response
    payload_size = len(
        event_delivery_payload_in_database.payload.get_payload().encode("utf-8")
    )
    global_attributes = {"global.attr": "value"}

    # when
    with set_global_attributes(global_attributes):
        _send_webhook_request_sync(event_delivery_payload_in_database)

    # then
    attributes = {
        "server.address": "www.example.com",
        "error.type": "request_error",
        "saleor.app.identifier": event_delivery_payload_in_database.webhook.app.identifier,
        "saleor.webhook.event_type": event_delivery_payload_in_database.event_type,
        "saleor.webhook.execution_mode": "sync",
        **global_attributes,
    }
    metrics_data = get_test_metrics_data()
    external_request_count = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_COUNT
    )
    assert external_request_count.value == 1
    assert external_request_count.attributes == attributes

    external_request_duration = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_DURATION
    )
    assert external_request_duration.attributes == attributes
    assert external_request_duration.count == 1
    assert external_request_duration.sum == webhook_response.duration

    external_request_content_length = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_BODY_SIZE
    )
    assert external_request_content_length.attributes == attributes
    assert external_request_content_length.count == 1
    assert external_request_content_length.sum == payload_size


def test_send_webhook_request_sync_record_external_request_with_unknown_webhook_scheme(
    event_delivery_payload_in_database,
    get_test_metrics_data,
):
    # given
    event_delivery_payload_in_database.webhook.target_url = (
        "unknown://www.example.com/test"
    )
    payload_size = len(
        event_delivery_payload_in_database.payload.get_payload().encode("utf-8")
    )
    global_attributes = {"global.attr": "value"}

    # when
    with set_global_attributes(global_attributes):
        with pytest.raises(ValueError, match=r"Unknown webhook scheme: 'unknown'"):
            _send_webhook_request_sync(event_delivery_payload_in_database)

    # then
    attributes = {
        "server.address": "www.example.com",
        "error.type": "request_error",
        "saleor.app.identifier": event_delivery_payload_in_database.webhook.app.identifier,
        "saleor.webhook.event_type": event_delivery_payload_in_database.event_type,
        "saleor.webhook.execution_mode": "sync",
        **global_attributes,
    }
    metrics_data = get_test_metrics_data()
    external_request_count = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_COUNT
    )
    assert external_request_count.value == 1
    assert external_request_count.attributes == attributes

    external_request_duration = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_DURATION
    )
    assert external_request_duration.attributes == attributes
    assert external_request_duration.count == 1
    assert external_request_duration.sum == 0

    external_request_content_length = get_metric_data_point(
        metrics_data, METRIC_EXTERNAL_REQUEST_BODY_SIZE
    )
    assert external_request_content_length.attributes == attributes
    assert external_request_content_length.count == 1
    assert external_request_content_length.sum == payload_size
