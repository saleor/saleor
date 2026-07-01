from unittest.mock import patch

from django.test import override_settings

from ...utils import get_sqs_message_group_id
from ..transport import maybe_send_webhooks_async

APPLY_ASYNC_PATH = (
    "saleor.webhook.transport.asynchronous.transport."
    "send_webhook_request_async.apply_async"
)


@override_settings(WEBHOOK_ASYNC_LEGACY_MODE=True)
@patch(APPLY_ASYNC_PATH)
def test_legacy_mode_enabled_schedules_celery_task(mock_apply_async, event_delivery):
    # given
    domain = "example.com"

    # when
    maybe_send_webhooks_async([event_delivery], domain=domain)

    # then
    mock_apply_async.assert_called_once()
    call = mock_apply_async.call_args
    assert call.kwargs["kwargs"]["event_delivery_id"] == event_delivery.pk
    assert call.kwargs["MessageGroupId"] == get_sqs_message_group_id(
        domain, app=event_delivery.webhook.app
    )


@override_settings(WEBHOOK_ASYNC_LEGACY_MODE=False)
@patch(APPLY_ASYNC_PATH)
def test_legacy_mode_disabled_does_schedule_celery_task(
    mock_apply_async, event_delivery
):
    # given
    domain = "example.com"

    # when
    maybe_send_webhooks_async([event_delivery], domain=domain)

    # then
    mock_apply_async.assert_not_called()
