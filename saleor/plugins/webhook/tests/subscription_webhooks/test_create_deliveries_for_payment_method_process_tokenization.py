import json

import graphene

from .....payment.interface import PaymentMethodProcessTokenizationRequestData
from .....webhook.event_types import WebhookEventSyncType
from ...tasks import create_deliveries_for_subscriptions

PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION = """
subscription{
  event{
    ...on PaymentMethodProcessTokenizationSession{
      id
      user{
        id
      }
      channel{
        id
      }
      data
    }
  }
}
"""


def test_payment_method_process_tokenization_without_data(
    payment_method_process_tokenization_app, customer_user, channel_USD
):
    # given
    webhook = payment_method_process_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION
    webhook.save()

    expected_id = "test_id"

    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_id,
        channel=channel_USD,
        data=None,
    )

    event_type = WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION

    # when
    delivery = create_deliveries_for_subscriptions(event_type, request_data, [webhook])[
        0
    ]

    # then
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "data": None,
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
        "id": expected_id,
    }


def test_payment_method_process_tokenization_with_data(
    payment_method_process_tokenization_app, customer_user, channel_USD
):
    # given
    webhook = payment_method_process_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION
    webhook.save()

    expected_data = {"data": {"foo": "bar"}}
    expected_id = "test_id"

    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_id,
        channel=channel_USD,
        data=expected_data,
    )

    event_type = WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION

    # when
    delivery = create_deliveries_for_subscriptions(event_type, request_data, [webhook])[
        0
    ]

    # then
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "data": expected_data,
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
        "id": expected_id,
    }
