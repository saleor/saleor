from unittest import mock

from ....core.models import EventDeliveryAttempt
from ....webhook.transport.utils import attempt_update
from ..tasks import send_webhook_request_async


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.attempt_update",
    wraps=attempt_update,
)
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
    mocked_attempt_update,
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

    assert attempt
    mocked_attempt_update.assert_called_once_with(
        attempt, webhook_response, with_save=False
    )
    # Update attempt with the webhook response to make sure that overvability was called
    # with up-to-date event
    attempt_update(attempt, webhook_response, with_save=False)
    mocked_observability.assert_called_once_with(attempt)
    mocked_clear_delivery.assert_called_once_with(event_delivery)
