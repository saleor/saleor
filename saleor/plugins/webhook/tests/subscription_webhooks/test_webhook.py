import dataclasses
from unittest import mock

from freezegun import freeze_time

from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook
from .....webhook.payloads import generate_meta, generate_requestor
from ...tasks import trigger_webhooks_async

TEST_ID = "test_id"


@dataclasses.dataclass
class FakeDelivery:
    id = TEST_ID


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async.delay")
@mock.patch("saleor.plugins.webhook.tasks.create_deliveries_for_subscriptions")
def test_trigger_webhooks_async_without_meta(
    mocked_create_deliveries_for_subscription,
    mocked_send_webhook_request,
    subscription_order_updated_webhook,
    order,
):
    webhook = subscription_order_updated_webhook
    webhook_type = WebhookEventAsyncType.ORDER_UPDATED
    mocked_create_deliveries_for_subscription.return_value = [FakeDelivery()]

    data = {"regular_webhook": "data"}
    trigger_webhooks_async(data, webhook_type, [webhook], order)
    mocked_create_deliveries_for_subscription.assert_called_once_with(
        event_type=webhook_type,
        subscribable_object=order,
        webhooks=[webhook],
        meta={},
    )
    mocked_send_webhook_request.assert_called_once_with(TEST_ID)


@freeze_time("2018-05-31 12:00:01")
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_async.delay")
@mock.patch("saleor.plugins.webhook.tasks.create_deliveries_for_subscriptions")
def test_trigger_webhooks_async_with_meta(
    mocked_create_deliveries_for_subscription,
    mocked_send_webhook_request,
    subscription_order_updated_webhook,
    order,
    staff_user,
):
    webhook = subscription_order_updated_webhook
    webhook_type = WebhookEventAsyncType.ORDER_UPDATED
    mocked_create_deliveries_for_subscription.return_value = [FakeDelivery()]
    data = {"regular_webhook": "data"}
    trigger_webhooks_async(data, webhook_type, [webhook], order, staff_user)
    mocked_create_deliveries_for_subscription.assert_called_once_with(
        event_type=webhook_type,
        subscribable_object=order,
        webhooks=[webhook],
        meta=generate_meta(
            requestor_data=generate_requestor(staff_user), camel_case=True
        ),
    )
    mocked_send_webhook_request.assert_called_once_with(TEST_ID)


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
