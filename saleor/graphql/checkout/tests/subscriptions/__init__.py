import json

import graphene

from .....checkout.webhooks import ShippingListMethodsForCheckout
from .....webhook.transport.asynchronous import create_deliveries_for_subscriptions


def test_shipping_list_methods_for_checkout(
    checkout_with_shipping_required,
    subscription_webhook,
    address,
    shipping_method,
):
    # given
    query = """
    subscription {
      event {
        ...on ShippingListMethodsForCheckout {
          checkout {
            id
          }
        }
      }
    }
    """
    event_type = ShippingListMethodsForCheckout.event_type
    webhook = subscription_webhook(query, event_type)
    checkout = checkout_with_shipping_required
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    webhooks = [webhook]
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)

    # then
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload["checkout"] == {"id": checkout_id}
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]
