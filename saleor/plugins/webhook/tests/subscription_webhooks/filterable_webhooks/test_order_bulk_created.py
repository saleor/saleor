import json

import graphene

from ......webhook.event_types import WebhookEventAsyncType
from ......webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)

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


def test_order_bulk_created(
    order_line, subscription_webhook, order_with_lines_channel_PLN
):
    # given
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()
    second_channel = order_with_lines_channel_PLN.channel
    second_channel.slug = "different-channel"
    second_channel.save()
    webhook = subscription_webhook(
        ORDER_BULK_CREATED_SUBSCRIPTION, WebhookEventAsyncType.ORDER_BULK_CREATED
    )

    event_type = WebhookEventAsyncType.ORDER_BULK_CREATED
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, [order, order_with_lines_channel_PLN], [webhook]
    )

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

    assert deliveries[0].payload.get_payload() == expected_payload
    assert len(deliveries) == 1
    assert deliveries[0].webhook == webhook


def test_order_bulk_created_without_channels_input(order_line, subscription_webhook):
    # given
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

    event_type = WebhookEventAsyncType.ORDER_BULK_CREATED
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type,
        [
            order,
        ],
        [webhook],
    )

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

    assert deliveries[0].payload.get_payload() == expected_payload
    assert len(deliveries) == 1
    assert deliveries[0].webhook == webhook


def test_order_bulk_created_with_different_channel(order_line, subscription_webhook):
    # given
    order = order_line.order
    channel = order.channel
    channel.slug = "different-channel"
    channel.save()
    webhook = subscription_webhook(
        ORDER_BULK_CREATED_SUBSCRIPTION, WebhookEventAsyncType.ORDER_BULK_CREATED
    )

    event_type = WebhookEventAsyncType.ORDER_BULK_CREATED

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, order, [webhook])

    # then
    assert deliveries == []


def test_different_event_doesnt_trigger_webhook(order_line, subscription_webhook):
    # given
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()
    webhook = subscription_webhook(
        ORDER_BULK_CREATED_SUBSCRIPTION, WebhookEventAsyncType.ORDER_CREATED
    )

    event_type = WebhookEventAsyncType.ORDER_CREATED

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, [order], [webhook])

    # then
    assert deliveries == []
