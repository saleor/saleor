import json

import graphene
import pytest

from .....shipping.interface import ShippingMethodData
from .....shipping.models import ShippingMethod
from .....shipping.utils import convert_to_shipping_method_data
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)
from .....webhook.transport.synchronous.transport import (
    create_delivery_for_subscription_sync_event,
)

SHIPPING_LIST_METHODS_FOR_CHECKOUT = """
subscription{
  event{
    ...on ShippingListMethodsForCheckout{
      checkout{
        id
      }
      shippingMethods{
        name
        id
      }
    }
  }
}
"""


@pytest.fixture
def subscription_shipping_list_methods_for_checkout_webhook(subscription_webhook):
    return subscription_webhook(
        SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )


@pytest.fixture
def subscription_checkout_shipping_filter_and_list_missing_one_in_definition(
    subscription_webhook,
):
    from .....webhook.tests.subscription_webhooks import (
        subscription_queries as queries,
    )

    return subscription_webhook(
        queries.THUMBNAIL_CREATED,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )


def test_shipping_list_methods_for_checkout(
    checkout_with_shipping_required,
    subscription_shipping_list_methods_for_checkout_webhook,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_shipping_required
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    webhooks = [subscription_shipping_list_methods_for_checkout_webhook]
    event_type = WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    internal_methods: list[ShippingMethodData] = []
    for method in ShippingMethod.objects.all():
        shipping_method_data = convert_to_shipping_method_data(
            method, method.channel_listings.get(channel=checkout.channel)
        )
        internal_methods.append(shipping_method_data)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, (checkout, internal_methods), webhooks
    )

    # then
    shipping_methods = [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", sm.id),
            "name": sm.name,
        }
        for sm in internal_methods
    ]
    payload = json.loads(deliveries[0].payload.get_payload())

    assert payload["checkout"] == {"id": checkout_id}
    for method in shipping_methods:
        assert method in payload["shippingMethods"]
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_list_methods_mismatch_in_subscription_query_definition(
    checkout_ready_to_complete,
    subscription_checkout_shipping_filter_and_list_missing_one_in_definition,
):
    # given
    webhook = subscription_checkout_shipping_filter_and_list_missing_one_in_definition
    event_type = WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout_ready_to_complete, webhook
    )

    # then
    assert not deliveries
