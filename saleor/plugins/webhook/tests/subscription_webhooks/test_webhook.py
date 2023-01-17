import dataclasses
import json
from unittest import mock

from .....core.models import EventDelivery
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.models import Webhook
from ...tasks import trigger_webhook_sync, trigger_webhooks_async
from .payloads import generate_payment_payload

TEST_ID = "test_id"


@dataclasses.dataclass
class FakeDelivery:
    id = TEST_ID


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async.delay")
def test_trigger_webhooks_async(
    mocked_send_webhook_request,
    webhook,
    subscription_order_created_webhook,
    order,
):
    webhook_type = WebhookEventAsyncType.ORDER_CREATED
    webhooks, payload = Webhook.objects.all(), {"example": "payload"}

    trigger_webhooks_async(payload, webhook_type, webhooks, order)

    deliveries = EventDelivery.objects.all()
    assert deliveries.count() == 2
    assert deliveries[0].webhook == subscription_order_created_webhook
    assert deliveries[1].webhook == webhook
    calls = [mock.call(deliveries[1].id), mock.call(deliveries[0].id)]
    assert mocked_send_webhook_request.mock_calls == calls


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


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_webhook_sync_with_subscription(
    mock_request, payment_app_with_subscription_webhooks, payment
):
    # given
    payment_app = payment_app_with_subscription_webhooks
    data = '{"key": "value"}'
    expected_payment_payload = generate_payment_payload(payment)
    # when
    trigger_webhook_sync(
        WebhookEventSyncType.PAYMENT_AUTHORIZE,
        data,
        payment_app.webhooks.first(),
        payment,
    )
    event_delivery = EventDelivery.objects.first()

    # then
    assert json.loads(event_delivery.payload.payload) == expected_payment_payload
    mock_request.assert_called_once_with(payment_app.name, event_delivery)
