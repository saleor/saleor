from unittest.mock import patch

from django.conf import settings
from django.test import override_settings

from ..transport import get_queue_name_for_webhook, maybe_send_webhooks_async

SEND_WEBHOOK_REQUEST_ASYNC_PATH = "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"


@override_settings(WEBHOOK_ASYNC_LEGACY_MODE=True)
@patch(SEND_WEBHOOK_REQUEST_ASYNC_PATH)
def test_dispatches_delivery_when_legacy_mode_enabled(
    mock_apply_async,
    event_delivery,
):
    # given
    domain = "example.com"

    # when
    maybe_send_webhooks_async([event_delivery], domain=domain)

    # then
    mock_apply_async.assert_called_once()
    call = mock_apply_async.call_args
    assert call.kwargs["kwargs"]["event_delivery_id"] == event_delivery.pk
    assert call.kwargs["queue"] == get_queue_name_for_webhook(
        event_delivery.webhook,
        default_queue=settings.WEBHOOK_CELERY_QUEUE_NAME,
    )


@override_settings(WEBHOOK_ASYNC_LEGACY_MODE=False)
@patch(SEND_WEBHOOK_REQUEST_ASYNC_PATH)
def test_does_not_dispatch_delivery_when_legacy_mode_disabled(
    mock_apply_async,
    event_delivery,
):
    # given
    domain = "example.com"

    # when
    maybe_send_webhooks_async([event_delivery], domain=domain)

    # then
    mock_apply_async.assert_not_called()
