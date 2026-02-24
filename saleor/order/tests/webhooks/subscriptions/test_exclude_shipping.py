import json

import graphene
import pytest

from .....shipping.models import ShippingMethodChannelListing
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.transport.synchronous.transport import (
    create_delivery_for_subscription_sync_event,
)
from ....delivery_context import get_all_shipping_methods_for_order

ORDER_FILTER_SHIPPING_METHODS = """
subscription{
  event{
    ...on OrderFilterShippingMethods{
      order{
        id
      }
      shippingMethods{
        id
        name
      }
    }
  }
}
"""

ORDER_FILTER_SHIPPING_METHODS_AVAILABLE_SHIPPING_METHODS = """
subscription{
  event{
    ...on OrderFilterShippingMethods{
      order{
        id
        availableShippingMethods{
          id
        }
      }
    }
  }
}
"""

ORDER_FILTER_SHIPPING_METHODS_CIRCULAR_SHIPPING_METHODS = """
subscription{
  event{
    ...on OrderFilterShippingMethods{
      order{
        id
        shippingMethods{
          id
        }
      }
    }
  }
}
"""


@pytest.fixture
def subscription_with_filter_shipping_methods_webhook(subscription_webhook):
    return subscription_webhook(
        ORDER_FILTER_SHIPPING_METHODS,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_with_shipping_methods(
    subscription_webhook,
):
    return subscription_webhook(
        ORDER_FILTER_SHIPPING_METHODS_CIRCULAR_SHIPPING_METHODS,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    )


@pytest.fixture
def subscription_with_available_ship_methods(
    subscription_webhook,
):
    return subscription_webhook(
        ORDER_FILTER_SHIPPING_METHODS_AVAILABLE_SHIPPING_METHODS,
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    )


def test_order_filter_shipping_methods(
    order_line_with_one_allocation,
    subscription_with_filter_shipping_methods_webhook,
    address,
):
    # given
    order = order_line_with_one_allocation.order
    order_line_with_one_allocation.is_shipping_required = True
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    order_id = graphene.Node.to_global_id("Order", order.pk)
    all_shipping_methods = get_all_shipping_methods_for_order(
        order, ShippingMethodChannelListing.objects.all()
    )

    # when
    delivery = create_delivery_for_subscription_sync_event(
        event_type,
        (order, all_shipping_methods),
        subscription_with_filter_shipping_methods_webhook,
    )

    # then
    shipping_methods = [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", sm.id),
            "name": sm.name,
        }
        for sm in all_shipping_methods
    ]
    payload = json.loads(delivery.payload.get_payload())

    assert payload["order"] == {"id": order_id}
    for method in shipping_methods:
        assert method in payload["shippingMethods"]

    assert delivery.webhook == subscription_with_filter_shipping_methods_webhook


def test_order_filter_shipping_methods_no_methods_in_channel(
    order_line_with_one_allocation,
    subscription_with_filter_shipping_methods_webhook,
    shipping_method_channel_PLN,
):
    # given
    order = order_line_with_one_allocation.order
    order.save(update_fields=["shipping_address"])

    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    delivery = create_delivery_for_subscription_sync_event(
        event_type, (order, []), subscription_with_filter_shipping_methods_webhook
    )

    # then
    expected_payload = {"order": {"id": order_id}, "shippingMethods": []}

    assert json.loads(delivery.payload.get_payload()) == expected_payload
    assert delivery.webhook == subscription_with_filter_shipping_methods_webhook


def test_order_filter_shipping_methods_with_circular_call_for_available_methods(
    order_line_with_one_allocation,
    subscription_with_available_ship_methods,
):
    # given
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    order = order_line_with_one_allocation.order

    # when
    delivery = create_delivery_for_subscription_sync_event(
        event_type,
        (order, []),
        subscription_with_available_ship_methods,
    )

    # then
    payload = json.loads(delivery.payload.get_payload())

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )


def test_order_filter_shipping_methods_with_circular_call_for_shipping_methods(
    order_line_with_one_allocation,
    subscription_with_shipping_methods,
):
    # given

    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    order = order_line_with_one_allocation.order

    # when
    delivery = create_delivery_for_subscription_sync_event(
        event_type,
        (order, []),
        subscription_with_shipping_methods,
    )

    # then
    payload = json.loads(delivery.payload.get_payload())

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )
    assert payload["order"] is None
