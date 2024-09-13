import json
from unittest import mock

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventDeliveryAttempt
from ..tasks import send_webhook_request_async


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.observability.report_event_delivery_attempt"
)
@mock.patch("saleor.webhook.transport.asynchronous.transport.clear_successful_delivery")
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhook_request_async(
    mocked_send_response,
    mocked_clear_delivery,
    mocked_observability,
    event_delivery,
    webhook_response,
):
    # given
    mocked_send_response.return_value = webhook_response

    # when
    send_webhook_request_async(event_delivery.pk)

    # then
    mocked_send_response.assert_called_once_with(
        event_delivery.webhook.target_url,
        "mirumee.com",
        event_delivery.webhook.secret_key,
        event_delivery.event_type,
        event_delivery.payload.payload,
        event_delivery.webhook.custom_headers,
    )
    mocked_clear_delivery.assert_called_once_with(event_delivery)
    attempt = EventDeliveryAttempt.objects.filter(delivery=event_delivery).first()
    delivery = EventDelivery.objects.get(id=event_delivery.pk)

    assert attempt
    assert delivery
    assert attempt.status == EventDeliveryStatus.SUCCESS
    assert attempt.response == webhook_response.content
    assert attempt.response_headers == json.dumps(webhook_response.response_headers)
    assert attempt.response_status_code == webhook_response.response_status_code
    assert attempt.request_headers == json.dumps(webhook_response.request_headers)
    assert attempt.duration == webhook_response.duration
    assert delivery.status == EventDeliveryStatus.SUCCESS
    mocked_observability.assert_called_once_with(attempt)
