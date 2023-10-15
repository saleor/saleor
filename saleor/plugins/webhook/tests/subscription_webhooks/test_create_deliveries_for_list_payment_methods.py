import json

import graphene

from .....payment.interface import ListStoredPaymentMethodsRequestData
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)

LIST_STORED_PAYMENT_METHODS = """
subscription {
  event {
    ... on ListStoredPaymentMethods{
      user{
        id
      }
      channel{
        id
      }
    }
  }
}
"""


def test_list_stored_payment_methods(
    list_stored_payment_methods_app,
    webhook_list_stored_payment_methods_response,
    channel_USD,
    customer_user,
):
    # given
    webhook = list_stored_payment_methods_app.webhooks.first()
    webhook.subscription_query = LIST_STORED_PAYMENT_METHODS
    webhook.save()

    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )

    event_type = WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS

    # when
    delivery = create_deliveries_for_subscriptions(event_type, data, [webhook])[0]

    # then
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
    }
