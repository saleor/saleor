from unittest import mock

from django.utils import timezone

from ....core.models import EventDelivery, EventPayload
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.transport.synchronous.transport import trigger_all_webhooks_sync
from ....webhook.transport.utils import parse_tax_data


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_not_trigger_sync_webhook_for_removed_app(
    mock_request,
    tax_checkout_webhook,
):
    # given
    app = tax_checkout_webhook.app
    app.removed_at = timezone.now()
    app.save(update_fields=["removed_at"])
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    trigger_all_webhooks_sync(event_type, lambda: data, parse_tax_data)

    # then
    assert EventPayload.objects.count() == 0
    assert EventDelivery.objects.count() == 0
    mock_request.assert_not_called()
