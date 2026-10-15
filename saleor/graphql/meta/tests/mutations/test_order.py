import json
from unittest.mock import ANY, patch

import graphene
import pytest
from django.test import override_settings

from .....core.models import EventDelivery
from .....order import OrderStatus
from .....payment.models import TransactionItem
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.models import WebhookPayloadGeneration
from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE
from .test_delete_metadata import (
    execute_clear_public_metadata_for_item,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_delete_public_metadata_for_order_by_id(
    staff_api_client, order, permission_manage_orders
):
    # given
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)
    old_updated_at = order.updated_at

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], order, order_id
    )
    order.refresh_from_db()
    assert order.updated_at > old_updated_at


def test_delete_public_metadata_for_order_by_token(
    staff_api_client, order, permission_manage_orders
):
    # given
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)
    old_updated_at = order.updated_at

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_orders, order.id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], order, order_id
    )
    order.refresh_from_db()
    assert order.updated_at > old_updated_at


def test_delete_public_metadata_for_draft_order_by_id(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["metadata"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    old_updated_at = draft_order.updated_at

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order_id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], draft_order, draft_order_id
    )
    draft_order.refresh_from_db()
    assert draft_order.updated_at > old_updated_at


def test_delete_public_metadata_for_draft_order_by_token(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["metadata"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    old_updated_at = draft_order.updated_at

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order.id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], draft_order, draft_order_id
    )
    draft_order.refresh_from_db()
    assert draft_order.updated_at > old_updated_at


def test_delete_public_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order_line.save(update_fields=["metadata"])
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_orders, order_line_id, "OrderLine"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], order_line, order_line_id
    )


def test_delete_private_metadata_for_order_by_id(
    staff_api_client, order, permission_manage_orders
):
    # given
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["private_metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)
    old_updated_at = order.updated_at

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], order, order_id
    )
    order.refresh_from_db()
    assert order.updated_at > old_updated_at


def test_delete_private_metadata_for_order_by_token(
    staff_api_client, order, permission_manage_orders
):
    # given
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["private_metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)
    old_updated_at = order.updated_at

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order.id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], order, order_id
    )
    order.refresh_from_db()
    assert order.updated_at > old_updated_at


def test_delete_private_metadata_for_draft_order_by_id(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["private_metadata"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    old_updated_at = draft_order.updated_at

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order_id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], draft_order, draft_order_id
    )
    draft_order.refresh_from_db()
    assert draft_order.updated_at > old_updated_at


def test_delete_private_metadata_for_draft_order_by_token(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["private_metadata"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    old_updated_at = draft_order.updated_at

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order.id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], draft_order, draft_order_id
    )
    draft_order.refresh_from_db()
    assert draft_order.updated_at > old_updated_at


def test_delete_private_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order_line.save(update_fields=["private_metadata"])
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_line_id, "OrderLine"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], order_line, order_line_id
    )


def test_add_public_metadata_for_order_by_id(
    staff_api_client, order, permission_manage_orders
):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)
    old_updated_at = order.updated_at

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], order, order_id
    )
    order.refresh_from_db()
    assert order.updated_at > old_updated_at


def test_add_public_metadata_for_order_by_token(
    staff_api_client, order, permission_manage_orders
):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)
    old_updated_at = order.updated_at

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, order.id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], order, order_id
    )
    order.refresh_from_db()
    assert order.updated_at > old_updated_at


def test_add_public_metadata_for_draft_order_by_id(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    old_updated_at = draft_order.updated_at

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order_id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], draft_order, draft_order_id
    )
    draft_order.refresh_from_db()
    assert draft_order.updated_at > old_updated_at


def test_add_public_metadata_for_draft_order_by_token(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    old_updated_at = draft_order.updated_at

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order.id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], draft_order, draft_order_id
    )
    draft_order.refresh_from_db()
    assert draft_order.updated_at > old_updated_at


def test_add_public_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, order_line_id, "OrderLine"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], order_line, order_line_id
    )


def test_update_public_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order_line.save(update_fields=["metadata"])
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_orders,
        order_line_id,
        "OrderLine",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        order_line,
        order_line_id,
        value="NewMetaValue",
    )


def test_add_private_metadata_for_order_by_id(
    staff_api_client, order, permission_manage_orders
):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)
    old_updated_at = order.updated_at

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], order, order_id
    )
    order.refresh_from_db()
    assert order.updated_at > old_updated_at


def test_add_private_metadata_for_order_by_token(
    staff_api_client, order, permission_manage_orders
):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)
    old_updated_at = order.updated_at

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order.id, "Order"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], order, order_id
    )
    order.refresh_from_db()
    assert order.updated_at > old_updated_at


def test_update_private_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order_line.save(update_fields=["private_metadata"])
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_orders,
        order_line_id,
        "OrderLine",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        order_line,
        order_line_id,
        value="NewMetaValue",
    )


def test_add_private_metadata_for_draft_order_by_id(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    old_updated_at = draft_order.updated_at

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order_id, "Order"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], draft_order, draft_order_id
    )
    draft_order.refresh_from_db()
    assert draft_order.updated_at > old_updated_at


def test_add_private_metadata_for_draft_order_by_token(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    old_updated_at = draft_order.updated_at

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order.id, "Order"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], draft_order, draft_order_id
    )
    draft_order.refresh_from_db()
    assert draft_order.updated_at > old_updated_at


def test_add_private_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_line_id, "OrderLine"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], order_line, order_line_id
    )


def test_delete_private_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_metadata"])
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], fulfillment, fulfillment_id
    )


def test_delete_public_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], fulfillment, fulfillment_id
    )


def test_delete_public_metadata_for_transaction_item(
    staff_api_client, permission_manage_payments
):
    # given
    transaction_item = TransactionItem.objects.create(
        metadata={PUBLIC_KEY: PUBLIC_VALUE}
    )
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_payments, transaction_id, "TransactionItem"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], transaction_item, transaction_id
    )


def test_add_public_metadata_for_transaction_item(
    staff_api_client,
    permission_manage_payments,
):
    # given
    transaction_item = TransactionItem.objects.create()
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_payments, transaction_id, "TransactionItem"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], transaction_item, transaction_id
    )


def test_add_public_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], fulfillment, fulfillment_id
    )


def test_add_private_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category_id = graphene.Node.to_global_id("Category", category.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, category_id, "Category"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], category, category_id
    )


def test_add_private_metadata_for_collection(
    staff_api_client, permission_manage_products, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, collection_id, "Collection"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], collection, collection_id
    )


def test_add_private_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], fulfillment, fulfillment_id
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_change_in_public_metadata_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    staff_api_client,
    order_with_lines,
    settings,
    permission_manage_orders,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks([WebhookEventAsyncType.ORDER_METADATA_UPDATED])

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order", key="new-key"
    )

    # then
    order_metadata_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_METADATA_UPDATED,
    )

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": order_metadata_updated_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

    filter_shipping_call = next(
        call
        for call in mocked_send_webhook_request_sync.mock_calls
        if call.args[0].webhook_id == shipping_filter_webhook.id
    )
    tax_delivery_call = next(
        call
        for call in mocked_send_webhook_request_sync.mock_calls
        if call.args[0].webhook_id == tax_webhook.id
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_change_in_private_metadata_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    settings,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks([WebhookEventAsyncType.ORDER_METADATA_UPDATED])

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order", key="new-key"
    )

    # then
    order_metadata_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_METADATA_UPDATED,
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": order_metadata_updated_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

    filter_shipping_call = next(
        call
        for call in mocked_send_webhook_request_sync.mock_calls
        if call.args[0].webhook_id == shipping_filter_webhook.id
    )
    tax_delivery_call = next(
        call
        for call in mocked_send_webhook_request_sync.mock_calls
        if call.args[0].webhook_id == tax_webhook.id
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )


ORDER_METADATA_UPDATED_METADATA_SUBSCRIPTION = """
    subscription {
      event {
        ... on OrderMetadataUpdated {
          order {
            id
            metadata {
              key
              value
            }
          }
        }
      }
    }
"""


@pytest.fixture
def order_metadata_subscription_webhook(subscription_webhook):
    return subscription_webhook(
        ORDER_METADATA_UPDATED_METADATA_SUBSCRIPTION,
        WebhookEventAsyncType.ORDER_METADATA_UPDATED,
    )


@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_consecutive_metadata_updates_immediate_webhook_carries_each_value(
    mocked_send_webhook_request_async,
    mocked_generate_deferred_payloads,
    order_metadata_subscription_webhook,
    staff_api_client,
    order,
    permission_manage_orders,
):
    # given
    webhook = order_metadata_subscription_webhook
    webhook.payload_generation = WebhookPayloadGeneration.IMMEDIATE
    webhook.save(update_fields=["payload_generation"])
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.pk)
    existing_metadata = dict(order.metadata)
    key = "status"
    first_value = "picking"
    second_value = "packed"

    # when
    execute_update_public_metadata_for_item(
        staff_api_client, None, order_id, "Order", key, first_value
    )
    execute_update_public_metadata_for_item(
        staff_api_client, None, order_id, "Order", key, second_value
    )

    # then - each delivery carries the metadata written by its own request
    mocked_generate_deferred_payloads.assert_not_called()
    deliveries = list(EventDelivery.objects.filter(webhook=webhook).order_by("pk"))
    assert len(deliveries) == 2
    first_payload = json.loads(deliveries[0].payload.get_payload())
    second_payload = json.loads(deliveries[1].payload.get_payload())
    assert {
        item["key"]: item["value"] for item in first_payload["order"]["metadata"]
    } == {**existing_metadata, key: first_value}
    assert {
        item["key"]: item["value"] for item in second_payload["order"]["metadata"]
    } == {**existing_metadata, key: second_value}
    assert mocked_send_webhook_request_async.call_count == 2


@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_consecutive_metadata_updates_deferred_webhook_defers_both_payloads(
    mocked_send_webhook_request_async,
    mocked_generate_deferred_payloads,
    order_metadata_subscription_webhook,
    staff_api_client,
    order,
    permission_manage_orders,
):
    # given
    webhook = order_metadata_subscription_webhook
    assert webhook.payload_generation == WebhookPayloadGeneration.DEFERRED
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.pk)
    key = "status"

    # when
    execute_update_public_metadata_for_item(
        staff_api_client, None, order_id, "Order", key, "picking"
    )
    execute_update_public_metadata_for_item(
        staff_api_client, None, order_id, "Order", key, "packed"
    )

    # then - no payload exists yet; both will be built from the final state
    deliveries = list(EventDelivery.objects.filter(webhook=webhook).order_by("pk"))
    assert len(deliveries) == 2
    assert [delivery.payload for delivery in deliveries] == [None, None]
    assert mocked_generate_deferred_payloads.call_count == 2
    mocked_send_webhook_request_async.assert_not_called()
