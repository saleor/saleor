import json
from decimal import Decimal

import graphene

from .....webhook.event_types import WebhookEventSyncType
from .....webhook.models import Webhook
from .....webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)

PAYMENT_GATEWAY_INITIALIZE_SESSION = """
subscription {
  event{
    ...on PaymentGatewayInitializeSession{
      data
      sourceObject{
        __typename
        ... on Checkout{
          id
          totalPrice{
            gross{
              amount
            }
          }
        }
        ... on Order{
          id
        }
      }
    }
  }
}
"""


def test_payment_gateway_initialize_session_checkout_with_data(
    checkout, webhook_app, permission_manage_payments
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=PAYMENT_GATEWAY_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = {"some": "json data"}
    amount = Decimal("10")

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, (checkout, payload_data, amount), [webhook]
    )[0]

    # then

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "data": payload_data,
        "sourceObject": {
            "__typename": "Checkout",
            "id": checkout_id,
            "totalPrice": {"gross": {"amount": 0.0}},
        },
    }


def test_payment_gateway_initialize_session_checkout_without_data(
    checkout, webhook_app, permission_manage_payments
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=PAYMENT_GATEWAY_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = None
    amount = Decimal("10")
    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, (checkout, payload_data, amount), [webhook]
    )[0]

    # then
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "data": None,
        "sourceObject": {
            "__typename": "Checkout",
            "id": checkout_id,
            "totalPrice": {"gross": {"amount": 0.0}},
        },
    }


def test_payment_gateway_initialize_session_order_with_data(
    order, webhook_app, permission_manage_payments
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=PAYMENT_GATEWAY_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = {"some": "json data"}
    amount = Decimal("10")

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, (order, payload_data, amount), [webhook]
    )[0]

    # then

    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "data": payload_data,
        "sourceObject": {"__typename": "Order", "id": order_id},
    }


def test_payment_gateway_initialize_session_order_without_data(
    order, webhook_app, permission_manage_payments
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=PAYMENT_GATEWAY_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = None
    amount = Decimal("10")

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, (order, payload_data, amount), [webhook]
    )[0]

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert delivery.payload
    assert delivery.payload.payload
    assert json.loads(delivery.payload.payload) == {
        "data": None,
        "sourceObject": {"__typename": "Order", "id": order_id},
    }
