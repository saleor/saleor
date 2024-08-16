import json
from unittest.mock import patch

import graphene
from django.test import override_settings

from ......core.models import EventDelivery
from ......webhook.event_types import WebhookEventAsyncType
from .....manager import get_plugins_manager

ORDER_BULK_CREATED_SUBSCRIPTION = """
subscription {
  orderBulkCreated(channels: ["default-channel"]) {
    orders {
      id
      number
      lines {
        id
        variant {
          id
        }
      }
    }
  }
}
"""


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_bulk_created(
    mocked_async, order_line, subscription_webhook, order_with_lines_channel_PLN
):
    # given
    manager = get_plugins_manager(False)
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()
    second_channel = order_with_lines_channel_PLN.channel
    second_channel.slug = "different-channel"
    second_channel.save()

    event_type = WebhookEventAsyncType.ORDER_BULK_CREATED

    webhook = subscription_webhook(ORDER_BULK_CREATED_SUBSCRIPTION, event_type)

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    manager.order_bulk_created([order, order_with_lines_channel_PLN])

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "orderBulkCreated": {
                    "orders": [
                        {
                            "id": order_id,
                            "number": str(order.number),
                            "lines": [
                                {
                                    "id": graphene.Node.to_global_id(
                                        "OrderLine", order_line.id
                                    ),
                                    "variant": {
                                        "id": graphene.Node.to_global_id(
                                            "ProductVariant", order_line.variant_id
                                        )
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        }
    )

    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].payload.get_payload() == expected_payload
    assert deliveries[0].webhook == webhook
    assert mocked_async.called


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_bulk_created_without_channels_input(
    mocked_async, order_line, subscription_webhook
):
    # given
    manager = get_plugins_manager(False)
    order = order_line.order

    query = """subscription {
      orderBulkCreated {
        orders {
          id
          number
          lines {
            id
            variant {
              id
            }
          }
        }
      }
    }"""
    webhook = subscription_webhook(query, WebhookEventAsyncType.ORDER_BULK_CREATED)

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    manager.order_bulk_created([order])

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "orderBulkCreated": {
                    "orders": [
                        {
                            "id": order_id,
                            "number": str(order.number),
                            "lines": [
                                {
                                    "id": graphene.Node.to_global_id(
                                        "OrderLine", order_line.id
                                    ),
                                    "variant": {
                                        "id": graphene.Node.to_global_id(
                                            "ProductVariant", order_line.variant_id
                                        )
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        }
    )

    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].payload.get_payload() == expected_payload
    assert deliveries[0].webhook == webhook
    assert mocked_async.called


@patch(
    "saleor.webhook.transport.asynchronous.transport.create_event_delivery_list_for_webhooks"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_bulk_created_with_different_channel(
    mocked_async,
    mocked_create_event_delivery_list_for_webhooks,
    order_line,
    subscription_webhook,
):
    # given
    manager = get_plugins_manager(False)
    order = order_line.order
    channel = order.channel
    channel.slug = "different-channel"
    channel.save()

    subscription_webhook(
        ORDER_BULK_CREATED_SUBSCRIPTION, WebhookEventAsyncType.ORDER_BULK_CREATED
    )

    # when
    manager.order_bulk_created([order])

    # then
    assert not mocked_async.called
    assert not mocked_create_event_delivery_list_for_webhooks.called
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 0


@patch(
    "saleor.webhook.transport.asynchronous.transport.create_event_delivery_list_for_webhooks"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_different_event_doesnt_trigger_webhook(
    mocked_async,
    mocked_create_event_delivery_list_for_webhooks,
    order_line,
    subscription_webhook,
):
    # given
    manager = get_plugins_manager(False)
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()
    subscription_webhook(
        ORDER_BULK_CREATED_SUBSCRIPTION, WebhookEventAsyncType.ORDER_CREATED
    )

    # when
    manager.order_bulk_created([order])

    # then
    assert not mocked_async.called
    assert not mocked_create_event_delivery_list_for_webhooks.called
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 0
