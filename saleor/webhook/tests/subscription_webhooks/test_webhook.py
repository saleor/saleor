import json
from unittest import mock

from ....core.models import EventDelivery
from ...event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...models import Webhook
from ...transport.asynchronous import trigger_webhooks_async
from ...transport.synchronous import trigger_webhook_sync
from .payloads import generate_payment_payload


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_trigger_webhooks_async(
    mocked_send_webhook_request,
    webhook,
    subscription_order_created_webhook,
    order,
):
    webhook_type = WebhookEventAsyncType.ORDER_CREATED
    webhooks, payload = Webhook.objects.all(), '{"example": "payload"}'

    trigger_webhooks_async(payload, webhook_type, webhooks, order, allow_replica=False)

    deliveries = EventDelivery.objects.all()
    assert deliveries.count() == 2
    assert deliveries[0].webhook == subscription_order_created_webhook
    assert deliveries[1].webhook == webhook
    for delivery in deliveries:
        assert (
            mock.call(
                kwargs={"event_delivery_id": delivery.id},
                queue=None,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            in mocked_send_webhook_request.mock_calls
        )


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.create_deliveries_for_subscriptions"
)
def test_trigger_webhooks_async_no_subscription_webhooks(
    mocked_create_deliveries_for_subscriptions,
    mocked_send_webhook_request,
    webhook,
    order,
):
    webhook_type = WebhookEventAsyncType.ORDER_UPDATED
    webhooks = Webhook.objects.all()
    data = '{"regular_webhook": "data"}'
    trigger_webhooks_async(data, webhook_type, webhooks, order, allow_replica=False)
    mocked_create_deliveries_for_subscriptions.assert_not_called()


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
        False,
        payment,
    )

    # then
    mock_request.assert_called_once()
    # TODO (PE-371): Assert EventDelivery DB object wasn't created

    delivery = mock_request.mock_calls[0].args[0]
    assert json.loads(delivery.payload.get_payload()) == expected_payment_payload

