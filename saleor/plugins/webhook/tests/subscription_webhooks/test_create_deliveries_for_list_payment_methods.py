import json
from decimal import Decimal

import graphene
from prices import Money

from .....payment.interface import ListPaymentMethodsData
from .....webhook.event_types import WebhookEventSyncType
from ...tasks import create_deliveries_for_subscriptions

LIST_PAYMENT_METHODS = """
subscription {
  event {
    ... on ListPaymentMethods{
      user{
        id
      }
      channel{
        id
      }
      value{
        amount
        currency
      }
    }
  }
}
"""


def test_list_payment_methods(
    list_payment_methods_app,
    webhook_list_payment_methods_response,
    channel_USD,
    customer_user,
):
    # given
    webhook = list_payment_methods_app.webhooks.first()
    webhook.subscription_query = LIST_PAYMENT_METHODS
    webhook.save()

    amount = 100.0
    currency = "USD"
    data = ListPaymentMethodsData(
        channel=channel_USD,
        user=customer_user,
        amount=Money(Decimal(amount), currency),
    )

    event_type = WebhookEventSyncType.LIST_PAYMENT_METHODS

    # when
    delivery = create_deliveries_for_subscriptions(event_type, data, [webhook])[0]

    # then
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        "value": {"amount": amount, "currency": currency},
    }
