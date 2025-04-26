import json
from unittest.mock import patch

import graphene
from django.test import override_settings

from ......core.models import EventDelivery
from ......graphql.webhook.subscription_query import SubscriptionQuery
from ......webhook.event_types import WebhookEventAsyncType
from .....manager import get_plugins_manager

CHECKOUT_METADATA_UPDATED_SUBSCRIPTION = """
subscription {
  checkoutMetadataUpdated(channels: ["%s"]) {
    checkout {
      id
      token
      metadata {
        key
        value
      }
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
def test_checkout_metadata_updated(
    mocked_async, checkout_with_item, subscription_webhook, settings
):
    # given
    manager = get_plugins_manager(False)
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    channel = checkout.channel
    assert channel.slug == settings.DEFAULT_CHANNEL_SLUG

    # Add metadata to checkout
    metadata_items = [{"key": "test_key", "value": "test_value"}]
    checkout.metadata_storage.metadata = {"test_key": "test_value"}
    checkout.metadata_storage.save(update_fields=["metadata"])

    event_type = WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED

    query = CHECKOUT_METADATA_UPDATED_SUBSCRIPTION % settings.DEFAULT_CHANNEL_SLUG
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    manager.checkout_metadata_updated(checkout)

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "checkoutMetadataUpdated": {
                    "checkout": {
                        "id": checkout_id,
                        "token": str(checkout.token),
                        "metadata": metadata_items,
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
@override_settings(
    PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"],
    CELERY_TASK_ALWAYS_EAGER=True,
)
def test_checkout_metadata_updated_without_channels_input(
    mocked_async, checkout_with_item, subscription_webhook
):
    # given
    manager = get_plugins_manager(False)
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()

    # Add metadata to checkout
    metadata_items = [{"key": "test_key", "value": "test_value"}]
    checkout.metadata_storage.metadata = {"test_key": "test_value"}
    checkout.metadata_storage.save(update_fields=["metadata"])

    event_type = WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED

    query = """subscription {
      checkoutMetadataUpdated {
        checkout {
          id
          token
          metadata {
            key
            value
          }
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
    manager.checkout_metadata_updated(checkout)

    # then
    expected_payload = json.dumps(
        {
            "data": {
                "checkoutMetadataUpdated": {
                    "checkout": {
                        "id": checkout_id,
                        "token": str(checkout.token),
                        "metadata": metadata_items,
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
def test_checkout_metadata_updated_with_different_channel(
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

    # Add metadata to checkout
    checkout.metadata_storage.metadata = {"test_key": "test_value"}
    checkout.metadata_storage.save(update_fields=["metadata"])

    event_type = WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED

    query = CHECKOUT_METADATA_UPDATED_SUBSCRIPTION % settings.DEFAULT_CHANNEL_SLUG
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    # when
    manager.checkout_metadata_updated(checkout)

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
@override_settings(
    PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"],
    CELERY_TASK_ALWAYS_EAGER=True,
)
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

    # Add metadata to checkout
    checkout.metadata_storage.metadata = {"test_key": "test_value"}
    checkout.metadata_storage.save(update_fields=["metadata"])

    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED

    query = CHECKOUT_METADATA_UPDATED_SUBSCRIPTION % settings.DEFAULT_CHANNEL_SLUG
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    # when
    manager.checkout_metadata_updated(checkout)

    # then
    assert not mocked_async.called
    assert not mocked_create_event_delivery_list_for_webhooks.called
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 0
