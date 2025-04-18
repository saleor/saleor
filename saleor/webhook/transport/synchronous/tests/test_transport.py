from unittest.mock import MagicMock, patch

from opentelemetry.trace import StatusCode

from .....core.models import EventDeliveryStatus
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
    mock_send_webhook_using_http.return_value = mock_response

    # when
    _send_webhook_request_sync(event_delivery_payload_in_database)

    # then
    mock_span.set_status.assert_called_once_with(
        StatusCode.ERROR,
    )
