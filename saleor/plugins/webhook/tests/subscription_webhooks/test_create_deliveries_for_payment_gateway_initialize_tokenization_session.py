import json

import graphene

from .....payment.interface import PaymentGatewayInitializeTokenizationRequestData
from .....webhook.event_types import WebhookEventSyncType
from ...tasks import create_deliveries_for_subscriptions

PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION = """
subscription {
  event {
    ... on PaymentGatewayInitializeTokenizationSession{
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


def test_payment_gateway_initialize_tokenization_without_data(
    payment_gateway_initialize_tokenization_app, customer_user, channel_USD
):
    # given
    webhook = payment_gateway_initialize_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION
    webhook.save()

    request_delete_data = PaymentGatewayInitializeTokenizationRequestData(
        user=customer_user,
        app_identifier=payment_gateway_initialize_tokenization_app.identifier,
        channel=channel_USD,
        data=None,
    )

    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, request_delete_data, [webhook]
    )[0]

    # then
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "data": None,
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
    }


def test_payment_gateway_initialize_tokenization_with_data(
    payment_gateway_initialize_tokenization_app, customer_user, channel_USD
):
    # given
    webhook = payment_gateway_initialize_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION
    webhook.save()

    expected_data = {"data": {"foo": "bar"}}

    request_delete_data = PaymentGatewayInitializeTokenizationRequestData(
        user=customer_user,
        app_identifier=payment_gateway_initialize_tokenization_app.identifier,
        channel=channel_USD,
        data=expected_data,
    )

    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, request_delete_data, [webhook]
    )[0]

    # then
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "data": expected_data,
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
    }
