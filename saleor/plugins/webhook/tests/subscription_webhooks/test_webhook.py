import dataclasses
import json
from decimal import Decimal
from unittest import mock

import graphene

from .....core.models import EventDelivery
from .....graphql.discount.enums import DiscountValueTypeEnum
from .....graphql.order.tests.mutations.test_order_discount import ORDER_DISCOUNT_ADD
from .....graphql.product.tests.mutations.test_product_create import (
    CREATE_PRODUCT_MUTATION,
)
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.models import Webhook
from .....webhook.transport.asynchronous.transport import trigger_webhooks_async
from .....webhook.transport.synchronous.transport import trigger_webhook_sync
from .payloads import generate_payment_payload

TEST_ID = "test_id"


@dataclasses.dataclass
class FakeDelivery:
    id = TEST_ID


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
    webhooks, payload = Webhook.objects.all(), {"example": "payload"}

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
    data = {"regular_webhook": "data"}
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
    event_delivery = EventDelivery.objects.first()

    # then
    assert json.loads(event_delivery.payload.payload) == expected_payment_payload
    mock_request.assert_called_once_with(event_delivery)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch("saleor.webhook.transport.synchronous.transport.get_webhooks_for_event")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_trigger_webhook_sync_with_subscription_within_mutation_use_default_db(
    mocked_generate_payload,
    mocked_get_webhooks_for_event,
    mocked_request,
    draft_order,
    app_api_client,
    permission_manage_orders,
    settings,
    subscription_calculate_taxes_for_order,
):
    # given
    webhook = subscription_calculate_taxes_for_order
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_get_webhooks_for_event.return_value = [webhook]
    variables = {
        "orderId": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "value": Decimal("50"),
        },
    }
    app_api_client.app.permissions.add(permission_manage_orders)

    # when
    app_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)

    # then
    mocked_generate_payload.assert_called_once()
    assert not mocked_generate_payload.call_args[1]["request"].allow_replica


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async"
)
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.generate_payload_from_subscription"
)
def test_trigger_webhook_async_with_subscription_use_main_db(
    mocked_generate_payload,
    mocked_get_webhooks_for_event,
    mocked_request,
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
    subscription_product_created_webhook,
    settings,
):
    # given
    webhook = subscription_product_created_webhook
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_get_webhooks_for_event.return_value = [webhook]

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
        }
    }

    # when
    staff_api_client.post_graphql(
        CREATE_PRODUCT_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    mocked_generate_payload.assert_called_once()
    assert not mocked_generate_payload.call_args[1]["request"].allow_replica
