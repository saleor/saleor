import dataclasses
from unittest import mock

from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook
from ...tasks import trigger_webhooks_async

TEST_ID = "test_id"


@dataclasses.dataclass
class FakeDelivery:
    id = TEST_ID


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async.delay")
@mock.patch("saleor.plugins.webhook.tasks.create_deliveries_for_subscriptions")
def test_trigger_webhooks_async_no_subscription_webhooks(
    mocked_create_deliveries_for_subscriptions,
    mocked_send_webhook_request,
    webhook,
    order,
):
    webhook_type = WebhookEventAsyncType.ORDER_UPDATED
    webhooks = Webhook.objects.all()
    data = {"regular_webhook": "data"}
    trigger_webhooks_async(data, webhook_type, webhooks, order)
    mocked_create_deliveries_for_subscriptions.assert_not_called()
