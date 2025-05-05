import json
from unittest.mock import patch

import graphene
from django.test import override_settings

from ......core.models import EventDelivery
from ......graphql.webhook.subscription_query import SubscriptionQuery
from ......webhook.event_types import WebhookEventAsyncType
from .....manager import get_plugins_manager

CHECKOUT_UPDATED_SUBSCRIPTION = """
subscription {
  checkoutUpdated(channels: ["%s"]) {
    checkout {
      id
      token
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
@override_settings(
    PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"],
    CELERY_TASK_ALWAYS_EAGER=True,
)
def test_checkout_updated(
    mocked_async,
    checkout_with_item,
    subscription_webhook,
    settings,
):
    # given
    manager = get_plugins_manager(False)
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()

    channel = checkout.channel
    assert channel.slug == settings.DEFAULT_CHANNEL_SLUG

    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED

    query = CHECKOUT_UPDATED_SUBSCRIPTION % settings.DEFAULT_CHANNEL_SLUG
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    manager.checkout_updated(checkout)

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "checkoutUpdated": {
                    "checkout": {
                        "id": checkout_id,
                        "token": str(checkout.token),
                        "lines": [
                            {
                                "id": graphene.Node.to_global_id(
                                    "CheckoutLine", checkout_line.id
                                ),
                                "variant": {
                                    "id": graphene.Node.to_global_id(
                                        "ProductVariant", checkout_line.variant_id
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
def test_checkout_updated_without_channels_input(
    mocked_async, checkout_with_item, subscription_webhook
):
    # given
    manager = get_plugins_manager(False)
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()

    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED

    query = """subscription {
      checkoutUpdated {
        checkout {
          id
          token
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

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    manager.checkout_updated(checkout)

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "checkoutUpdated": {
                    "checkout": {
                        "id": checkout_id,
                        "token": str(checkout.token),
                        "lines": [
                            {
                                "id": graphene.Node.to_global_id(
                                    "CheckoutLine", checkout_line.id
                                ),
                                "variant": {
                                    "id": graphene.Node.to_global_id(
                                        "ProductVariant", checkout_line.variant_id
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
@override_settings(
    PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"],
    CELERY_TASK_ALWAYS_EAGER=True,
)
def test_checkout_updated_with_different_channel(
    mocked_async,
    mocked_create_event_delivery_list_for_webhooks,
    checkout_JPY_with_item,
    subscription_webhook,
    settings,
):
    # given
    manager = get_plugins_manager(False)
    checkout = checkout_JPY_with_item
    channel = checkout.channel
    assert channel.slug != settings.DEFAULT_CHANNEL_SLUG

    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED

    query = CHECKOUT_UPDATED_SUBSCRIPTION % settings.DEFAULT_CHANNEL_SLUG
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    # when
    manager.checkout_updated(checkout)

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
    checkout_with_item,
    subscription_webhook,
    settings,
):
    # given
    manager = get_plugins_manager(False)
    checkout = checkout_with_item
    channel = checkout.channel
    assert channel.slug == settings.DEFAULT_CHANNEL_SLUG

    event_type = WebhookEventAsyncType.CHECKOUT_CREATED

    query = CHECKOUT_UPDATED_SUBSCRIPTION % settings.DEFAULT_CHANNEL_SLUG
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    # when
    manager.checkout_updated(checkout)

    # then
    assert not mocked_async.called
    assert not mocked_create_event_delivery_list_for_webhooks.called
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 0
