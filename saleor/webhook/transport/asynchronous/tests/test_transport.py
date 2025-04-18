from unittest.mock import MagicMock, patch

from opentelemetry.trace import StatusCode

from .....core.models import EventDeliveryStatus
from ...utils import WebhookResponse
from ..transport import send_webhook_request_async


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch("saleor.webhook.transport.asynchronous.transport.webhooks_otel_trace")
@patch("saleor.webhook.transport.asynchronous.transport.attempt_update")
@patch("saleor.webhook.transport.asynchronous.transport.handle_webhook_retry")
def test_send_webhook_request_async_set_span_status_failed(
    mock_handle_webhook_retry,
    mock_attempt_update,
    mock_webhooks_otel_trace,
    mock_send_webhook_using_scheme_method,
    event_delivery_payload_in_database,
):
    # given
    event_delivery_id = event_delivery_payload_in_database.id
    mock_span = MagicMock()
    mock_webhooks_otel_trace.return_value.__enter__.return_value = mock_span

    mock_response = MagicMock(spec=WebhookResponse)
    mock_response.response_status_code = 500
    mock_response.status = EventDeliveryStatus.FAILED
    mock_response.content = ""
    mock_send_webhook_using_scheme_method.return_value = mock_response

    # when
    send_webhook_request_async(
        event_delivery_id=event_delivery_id, telemetry_context={}
    )

    # then
    mock_span.set_status.assert_called_once_with(
        StatusCode.ERROR,
    )
