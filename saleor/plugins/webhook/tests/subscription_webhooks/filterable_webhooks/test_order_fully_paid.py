import json
from unittest import mock

import graphene

from ......core.models import EventDelivery
from ......webhook.event_types import WebhookEventAsyncType
from ......webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
    trigger_webhooks_async,
)

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


def test_order_fully_paid(order_line, subscription_webhook):
    # given
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()

    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, order, [webhook])

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

    assert deliveries[0].payload.get_payload() == expected_payload
    assert len(deliveries) == 1
    assert deliveries[0].webhook == webhook


def test_order_fully_paid_without_channels_input(order_line, subscription_webhook):
    # given
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

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, order, [webhook])

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

    assert deliveries[0].payload.get_payload() == expected_payload
    assert len(deliveries) == 1
    assert deliveries[0].webhook == webhook


def test_order_fully_paid_with_different_channel(order_line, subscription_webhook):
    # given
    order = order_line.order
    channel = order.channel
    channel.slug = "different-channel"
    channel.save()

    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)

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

    event_type = WebhookEventAsyncType.ORDER_CREATED

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, order, [webhook])

    # then
    assert deliveries == []


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_trigger_filterable_webhook(
    mocked_apply_async, order_line, subscription_webhook
):
    # given
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()

    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)

    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    trigger_webhooks_async(None, event_type, [webhook], order, allow_replica=False)

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
    delivery = EventDelivery.objects.get()
    assert delivery.payload.get_payload() == expected_payload
    mocked_apply_async.assert_called_once_with(
        kwargs={"event_delivery_id": delivery.id},
        queue=None,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_dont_trigger_filterable_webhook_for_different_channel(
    mocked_apply_async, order_line, subscription_webhook
):
    # given
    order = order_line.order
    channel = order.channel
    channel.slug = "different-channel"
    channel.save()

    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)

    # when
    trigger_webhooks_async(None, event_type, [webhook], order, allow_replica=False)

    # then
    assert not mocked_apply_async.called
    assert not EventDelivery.objects.first()


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_dont_trigger_filterable_webhook_for_different_event(
    mocked_apply_async, order_line, subscription_webhook
):
    # given
    order = order_line.order
    channel = order.channel
    channel.slug = "default-channel"
    channel.save()

    event_type = WebhookEventAsyncType.ORDER_UPDATED

    webhook = subscription_webhook(ORDER_FULLY_PAID_SUBSCRIPTION, event_type)

    # when
    trigger_webhooks_async(None, event_type, [webhook], order, allow_replica=False)

    # then
    assert not mocked_apply_async.called
    assert not EventDelivery.objects.first()
