import json
from unittest.mock import patch

import graphene
from django.test import override_settings

from ......core.models import EventDelivery
from ......graphql.webhook.subscription_query import SubscriptionQuery
from ......webhook.event_types import WebhookEventAsyncType
from .....manager import get_plugins_manager

ORDER_FULLY_PAID_SUBSCRIPTION = """
subscription {
  orderFullyPaid(channels: ["default-channel"]) {
    order {
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
def test_order_fully_paid(mocked_async, order_line, subscription_webhook):
    # given
    manager = get_plugins_manager(False)
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()

    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)
    subscription_query = SubscriptionQuery(ORDER_FULLY_PAID_SUBSCRIPTION)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    manager.order_fully_paid(order)

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "orderFullyPaid": {
                    "order": {
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
def test_order_fully_paid_without_channels_input(
    mocked_async, order_line, subscription_webhook
):
    # given
    manager = get_plugins_manager(False)
    order = order_line.order

    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID

    query = """subscription {
      orderFullyPaid {
        order {
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
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    manager.order_fully_paid(order)

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "orderFullyPaid": {
                    "order": {
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
def test_order_fully_paid_with_different_channel(
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

    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)
    subscription_query = SubscriptionQuery(ORDER_FULLY_PAID_SUBSCRIPTION)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    # when
    manager.order_fully_paid(order)

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

    event_type = WebhookEventAsyncType.ORDER_CREATED

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)
    subscription_query = SubscriptionQuery(ORDER_FULLY_PAID_SUBSCRIPTION)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    # when
    manager.order_fully_paid(order)

    # then
    assert not mocked_async.called
    assert not mocked_create_event_delivery_list_for_webhooks.called
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 0
