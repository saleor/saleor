import json
from unittest.mock import patch

import graphene
from django.test import override_settings

from ......core.models import EventDelivery
from ......webhook.event_types import WebhookEventAsyncType
from .....manager import get_plugins_manager

ORDER_METADATA_UPDATED_SUBSCRIPTION = """
subscription {
  orderMetadataUpdated(channels: ["default-channel"]) {
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
def test_order_metadata_updated(mocked_async, order_line, subscription_webhook):
    # given
    manager = get_plugins_manager(False)
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()

    event_type = WebhookEventAsyncType.ORDER_METADATA_UPDATED

    webhook = subscription_webhook(ORDER_METADATA_UPDATED_SUBSCRIPTION, event_type)

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    manager.order_metadata_updated(order)

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "orderMetadataUpdated": {
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
def test_order_metadata_updated_without_channels_input(
    mocked_async, order_line, subscription_webhook
):
    # given
    manager = get_plugins_manager(False)
    order = order_line.order

    event_type = WebhookEventAsyncType.ORDER_METADATA_UPDATED

    query = """subscription {
      orderMetadataUpdated {
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

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    manager.order_metadata_updated(order)

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "orderMetadataUpdated": {
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
def test_order_metadata_updated_with_different_channel(
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

    event_type = WebhookEventAsyncType.ORDER_METADATA_UPDATED

    subscription_webhook(ORDER_METADATA_UPDATED_SUBSCRIPTION, event_type)

    # when
    manager.order_metadata_updated(order)

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

    subscription_webhook(ORDER_METADATA_UPDATED_SUBSCRIPTION, event_type)

    # when
    manager.order_metadata_updated(order)

    # then
    assert not mocked_async.called
    assert not mocked_create_event_delivery_list_for_webhooks.called
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 0
