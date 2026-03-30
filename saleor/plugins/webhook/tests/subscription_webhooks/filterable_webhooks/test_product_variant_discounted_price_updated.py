import json
from decimal import Decimal
from unittest.mock import patch

import graphene
from django.test import override_settings

from ......core.models import EventDelivery
from ......graphql.webhook.subscription_query import SubscriptionQuery
from ......product.interface import VariantDiscountedPriceChange
from ......webhook.event_types import WebhookEventAsyncType
from .....manager import get_plugins_manager

PRICE_UPDATED_SUBSCRIPTION = """
subscription {
  productVariantDiscountedPriceUpdated(channels: ["%s"]) {
    ... on ProductVariantDiscountedPriceUpdated {
      productVariant {
        id
        pricing {
          price {
            gross {
              amount
            }
          }
        }
      }
      channel {
        slug
      }
      previousPrice {
        amount
        currency
      }
      newPrice {
        amount
        currency
      }
    }
  }
}"""


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_product_variant_discounted_price_updated(
    mocked_async, variant_with_many_stocks, channel_USD, subscription_webhook
):
    # given
    manager = get_plugins_manager(False)
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED

    query = PRICE_UPDATED_SUBSCRIPTION % channel_USD.slug
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    previous_price = Decimal("10.00")
    new_price = Decimal("8.00")
    currency = channel_USD.currency_code

    price_info = VariantDiscountedPriceChange(
        variant_id=variant.id,
        channel_slug=channel_USD.slug,
        previous_price_amount=previous_price,
        new_price_amount=new_price,
        currency=currency,
    )

    # when
    manager.product_variant_discounted_price_updated(price_info)

    # then
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    payload = json.loads(deliveries[0].payload.get_payload())
    event_data = payload["data"]["productVariantDiscountedPriceUpdated"]
    assert event_data["productVariant"]["id"] == variant_id
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    assert (
        event_data["productVariant"]["pricing"]["price"]["gross"]["amount"]
        == variant_channel_listing.discounted_price_amount
    )
    assert event_data["channel"] == {"slug": channel_USD.slug}
    assert event_data["previousPrice"] == {
        "amount": previous_price,
        "currency": currency,
    }
    assert event_data["newPrice"] == {"amount": new_price, "currency": currency}
    assert deliveries[0].webhook == webhook
    assert mocked_async.called


@patch(
    "saleor.webhook.transport.asynchronous.transport.create_event_delivery_list_for_webhooks"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_product_variant_discounted_price_updated_with_different_channel(
    mocked_async,
    mocked_create_event_delivery_list_for_webhooks,
    variant_with_many_stocks,
    channel_USD,
    channel_PLN,
    subscription_webhook,
):
    # given
    manager = get_plugins_manager(False)
    variant = variant_with_many_stocks

    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED

    query = PRICE_UPDATED_SUBSCRIPTION % channel_PLN.slug
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    price_info = VariantDiscountedPriceChange(
        variant_id=variant.id,
        channel_slug=channel_USD.slug,
        previous_price_amount=Decimal("10.00"),
        new_price_amount=Decimal("8.00"),
        currency=channel_USD.currency_code,
    )

    # when
    manager.product_variant_discounted_price_updated(price_info)

    # then
    assert not mocked_async.called
    assert not mocked_create_event_delivery_list_for_webhooks.called
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 0


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_product_variant_discounted_price_updated_without_channels_input(
    mocked_async, variant_with_many_stocks, channel_USD, subscription_webhook
):
    # given
    manager = get_plugins_manager(False)
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DISCOUNTED_PRICE_UPDATED

    query = """subscription {
      productVariantDiscountedPriceUpdated {
        ... on ProductVariantDiscountedPriceUpdated {
          productVariant {
            id
          }
          channel {
            slug
          }
          previousPrice {
            amount
            currency
          }
          newPrice {
            amount
            currency
          }
        }
      }
    }"""
    webhook = subscription_webhook(query, event_type)
    subscription_query = SubscriptionQuery(query)
    webhook.filterable_channel_slugs = subscription_query.get_filterable_channel_slugs()
    webhook.save()

    previous_price = Decimal("10.00")
    new_price = Decimal("8.00")
    currency = channel_USD.currency_code

    price_info = VariantDiscountedPriceChange(
        variant_id=variant.id,
        channel_slug=channel_USD.slug,
        previous_price_amount=previous_price,
        new_price_amount=new_price,
        currency=currency,
    )

    # when
    manager.product_variant_discounted_price_updated(price_info)

    # then
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    payload = json.loads(deliveries[0].payload.get_payload())
    event_data = payload["data"]["productVariantDiscountedPriceUpdated"]
    assert event_data["productVariant"]["id"] == variant_id
    assert event_data["channel"] == {"slug": channel_USD.slug}
    assert event_data["previousPrice"] == {
        "amount": previous_price,
        "currency": currency,
    }
    assert event_data["newPrice"] == {"amount": new_price, "currency": currency}
    assert deliveries[0].webhook == webhook
    assert mocked_async.called
