from unittest.mock import patch

import pytest
from celery.exceptions import Retry as CeleryTaskRetryError
from opentelemetry.trace import StatusCode

from .....tests.utils import get_metric_data_point, get_span_by_name
from ...metrics import (
    METRIC_EXTERNAL_REQUEST_BODY_SIZE,
    METRIC_EXTERNAL_REQUEST_COUNT,
    METRIC_EXTERNAL_REQUEST_DURATION,
)
from ..transport import send_webhook_request_async


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async_set_span_status_failed(
    mock_send_webhook_using_scheme_method,
    event_delivery,
    webhook_response_failed,
    get_test_spans,
):
    # given
    mock_send_webhook_using_scheme_method.return_value = webhook_response_failed
    span_name = f"webhooks.{event_delivery.event_type}"

    # when
    with pytest.raises(CeleryTaskRetryError):
        send_webhook_request_async(
            event_delivery_id=event_delivery.id, telemetry_context={}
        )

    # then
    span = get_span_by_name(get_test_spans(), span_name)
    assert span.status.status_code == StatusCode.ERROR


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async_record_external_request(
    mock_send_webhook_using_scheme_method,
    event_delivery,
    webhook_response,
    get_test_metrics_data,
):
    # given
    mock_send_webhook_using_scheme_method.return_value = webhook_response
    payload_size = len(event_delivery.payload.get_payload().encode("utf-8"))
    global_attributes = {"global.attr": "value"}

    # when
    send_webhook_request_async(
        event_delivery_id=event_delivery.id,
        telemetry_context={"global_attributes": global_attributes},
    )

    # then
    attributes = {
        "server.address": "www.example.com",
        "saleor.app.identifier": event_delivery.webhook.app.identifier,
        "saleor.webhook.event_type": event_delivery.event_type,
        "saleor.webhook.execution_mode": "async",
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


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async_record_external_request_when_delivery_attempt_failed(
    mock_send_webhook_using_scheme_method,
    event_delivery,
    webhook_response_failed,
    get_test_metrics_data,
):
    # given
    mock_send_webhook_using_scheme_method.return_value = webhook_response_failed
    payload_size = len(event_delivery.payload.get_payload().encode("utf-8"))
    global_attributes = {"global.attr": "value"}

    # when
    with pytest.raises(CeleryTaskRetryError):
        send_webhook_request_async(
            event_delivery_id=event_delivery.id,
            telemetry_context={"global_attributes": global_attributes},
        )

    # then
    attributes = {
        "server.address": "www.example.com",
        "error.type": "request_error",
        "saleor.app.identifier": event_delivery.webhook.app.identifier,
        "saleor.webhook.event_type": event_delivery.event_type,
        "saleor.webhook.execution_mode": "async",
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


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async_record_external_request_with_unknown_webhook_scheme(
    mock_send_webhook_using_scheme_method,
    event_delivery,
    get_test_metrics_data,
):
    # given
    mock_send_webhook_using_scheme_method.side_effect = ValueError(
        "Unknown webhook scheme: unknown"
    )
    payload_size = len(event_delivery.payload.get_payload().encode("utf-8"))
    global_attributes = {"global.attr": "value"}

    # when
    send_webhook_request_async(
        event_delivery_id=event_delivery.id,
        telemetry_context={"global_attributes": global_attributes},
    )

    # then
    attributes = {
        "server.address": "www.example.com",
        "error.type": "request_error",
        "saleor.app.identifier": event_delivery.webhook.app.identifier,
        "saleor.webhook.event_type": event_delivery.event_type,
        "saleor.webhook.execution_mode": "async",
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


@patch("saleor.webhook.transport.asynchronous.transport.webhooks_otel_trace")
def test_send_webhook_request_async_fails_when_exception_raised_by_webhooks_otel_trace(
    mock_webhooks_otel_trace,
    event_delivery,
):
    # given
    mock_webhooks_otel_trace.side_effect = ValueError("OTel error")

    # when & then
    with pytest.raises(ValueError, match="OTel error"):
        send_webhook_request_async(
            event_delivery_id=event_delivery.id, telemetry_context={}
        )
