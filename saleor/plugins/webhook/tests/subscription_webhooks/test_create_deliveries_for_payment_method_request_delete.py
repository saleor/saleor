import json

import graphene

from .....payment.interface import PaymentMethodRequestDeleteData
from .....webhook.event_types import WebhookEventSyncType
from ...tasks import create_deliveries_for_subscriptions

PAYMENT_METHOD_REQUEST_DELETE = """
subscription {
  event {
    ... on PaymentMethodRequestDelete{
      user{
        id
      }
      paymentMethodId
    }
  }
}
"""


def test_payment_method_request_delete(
    payment_method_request_delete_app, customer_user
):
    # given
    webhook = payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = PAYMENT_METHOD_REQUEST_DELETE
    webhook.save()

    payment_method_id = "123"

    request_delete_data = PaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=payment_method_id,
    )

    event_type = WebhookEventSyncType.PAYMENT_METHOD_REQUEST_DELETE

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, request_delete_data, [webhook]
    )[0]

    # then
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "paymentMethodId": payment_method_id,
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
    }
