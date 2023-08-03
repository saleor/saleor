import json

import graphene

from .....payment.interface import StoredPaymentMethodRequestDeleteData
from .....webhook.event_types import WebhookEventSyncType
from ...tasks import create_deliveries_for_subscriptions

STORED_PAYMENT_METHOD_REQUEST_DELETE = """
subscription {
  event {
    ... on StoredPaymentMethodRequestDelete{
      user{
        id
      }
      paymentMethodId
    }
  }
}
"""


def test_stored_payment_method_request_delete(
    stored_payment_method_request_delete_app, customer_user
):
    # given
    webhook = stored_payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = STORED_PAYMENT_METHOD_REQUEST_DELETE
    webhook.save()

    payment_method_id = "123"

    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=payment_method_id,
    )

    event_type = WebhookEventSyncType.STORED_PAYMENT_METHOD_REQUEST_DELETE

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
