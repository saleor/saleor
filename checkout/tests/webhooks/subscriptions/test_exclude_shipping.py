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

CHECKOUT_FILTER_SHIPPING_METHODS = """
subscription{
  event{
    ...on CheckoutFilterShippingMethods{
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

CHECKOUT_FILTER_SHIPPING_METHODS_CIRCULAR_SHIPPING_METHODS = """
subscription{
  event{
    ...on CheckoutFilterShippingMethods{
      checkout{
        id
        shippingMethods{
          id
        }
      }
    }
  }
}
"""

CHECKOUT_FILTER_SHIPPING_METHODS_AVAILABLE_SHIPPING_METHODS = """
subscription{
  event{
    ...on CheckoutFilterShippingMethods{
      checkout{
        id
        availableShippingMethods{
          id
        }
      }
    }
  }
}
"""

CHECKOUT_FILTER_SHIPPING_METHODS_AVAILABLE_PAYMENT_GATEWAYS = """
subscription{
  event{
    ...on CheckoutFilterShippingMethods{
      checkout{
        id
        availablePaymentGateways{
          id
        }
      }
    }
  }
}
"""


@pytest.fixture
def subscription_checkout_filter_shipping_methods_webhook(subscription_webhook):
    return subscription_webhook(
        CHECKOUT_FILTER_SHIPPING_METHODS,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_checkout_filter_shipping_method_webhook_with_shipping_methods(
    subscription_webhook,
):
    return subscription_webhook(
        CHECKOUT_FILTER_SHIPPING_METHODS_CIRCULAR_SHIPPING_METHODS,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_checkout_filter_shipping_method_webhook_with_available_ship_methods(
    subscription_webhook,
):
    return subscription_webhook(
        CHECKOUT_FILTER_SHIPPING_METHODS_AVAILABLE_SHIPPING_METHODS,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_checkout_filter_shipping_method_webhook_with_payment_gateways(
    subscription_webhook,
):
    return subscription_webhook(
        CHECKOUT_FILTER_SHIPPING_METHODS_AVAILABLE_PAYMENT_GATEWAYS,
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )


def test_checkout_filter_shipping_methods(
    checkout_with_shipping_required,
    subscription_checkout_filter_shipping_methods_webhook,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_shipping_required
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    webhooks = [subscription_checkout_filter_shipping_methods_webhook]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
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


def test_checkout_filter_shipping_methods_no_methods_in_channel(
    checkout,
    subscription_checkout_filter_shipping_methods_webhook,
    address,
    shipping_method,
    shipping_method_channel_PLN,
):
    # given
    webhooks = [subscription_checkout_filter_shipping_methods_webhook]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, (checkout, []), webhooks
    )

    # then
    expected_payload = {"checkout": {"id": checkout_id}, "shippingMethods": []}
    assert json.loads(deliveries[0].payload.get_payload()) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_filter_shipping_methods_with_circular_call_for_shipping_methods(
    checkout_ready_to_complete,
    subscription_checkout_filter_shipping_method_webhook_with_shipping_methods,
):
    # given
    webhooks = [
        subscription_checkout_filter_shipping_method_webhook_with_shipping_methods
    ]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, (checkout_ready_to_complete, []), webhooks
    )

    # then
    payload = json.loads(deliveries[0].payload.get_payload())

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )
    assert payload["checkout"] is None


def test_checkout_filter_shipping_methods_with_available_shipping_methods_field(
    checkout_ready_to_complete,
    subscription_checkout_filter_shipping_method_webhook_with_available_ship_methods,
):
    # given
    webhooks = [
        subscription_checkout_filter_shipping_method_webhook_with_available_ship_methods
    ]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, (checkout_ready_to_complete, []), webhooks
    )

    # then
    payload = json.loads(deliveries[0].payload.get_payload())

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )
    assert payload["checkout"] is None


def test_checkout_filter_shipping_methods_with_circular_call_for_available_gateways(
    checkout_ready_to_complete,
    subscription_checkout_filter_shipping_method_webhook_with_payment_gateways,
):
    # given
    webhooks = [
        subscription_checkout_filter_shipping_method_webhook_with_payment_gateways
    ]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, (checkout_ready_to_complete, []), webhooks
    )

    # then
    payload = json.loads(deliveries[0].payload.get_payload())

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )
    assert payload["checkout"] is None
