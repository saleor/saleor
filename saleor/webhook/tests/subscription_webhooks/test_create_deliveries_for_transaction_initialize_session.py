import json
import uuid
from decimal import Decimal

import graphene

from ....channel import TransactionFlowStrategy
from ....payment.interface import (
    PaymentGatewayData,
    TransactionProcessActionData,
    TransactionSessionData,
)
from ...event_types import WebhookEventSyncType
from ...models import Webhook
from ...transport.asynchronous import create_deliveries_for_subscriptions

TRANSACTION_INITIALIZE_SESSION = """
subscription {
  event{
    ...on TransactionInitializeSession{
      merchantReference
      action{
        amount
        currency
        actionType
      }
      data
      customerIpAddress
      idempotencyKey
      sourceObject{
        __typename
        ... on Checkout{
          id
          user{
            id
          }
          totalPrice{
            gross{
              amount
            }
          }
        }
        ... on Order{
          id
          user{
            id
          }
        }
      }
    }
  }
}
"""


def test_transaction_initialize_session_checkout_with_data(
    checkout,
    webhook_app,
    permission_manage_payments,
    transaction_item_generator,
    customer_user,
):
    # given
    checkout.user = customer_user
    checkout.save()

    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=TRANSACTION_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = {"some": "json data"}
    amount = Decimal(10)
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        app=webhook_app,
        psp_reference=None,
        name=None,
        message=None,
    )
    action_type = TransactionFlowStrategy.CHARGE
    idempotency_key = str(uuid.uuid4())

    subscribable_object = TransactionSessionData(
        transaction=transaction,
        source_object=checkout,
        action=TransactionProcessActionData(
            amount=amount,
            currency=transaction.currency,
            action_type=action_type,
        ),
        customer_ip_address="127.0.0.1",
        payment_gateway_data=PaymentGatewayData(
            app_identifier=webhook_app.identifier, data=payload_data, error=None
        ),
        idempotency_key=idempotency_key,
    )

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, subscribable_object, [webhook]
    )[0]

    # then

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert delivery.payload
    assert delivery.payload.get_payload()
    assert json.loads(delivery.payload.get_payload()) == {
        "merchantReference": graphene.Node.to_global_id(
            "TransactionItem", transaction.token
        ),
        "action": {
            "amount": amount,
            "currency": "USD",
            "actionType": action_type.upper(),
        },
        "idempotencyKey": idempotency_key,
        "data": payload_data,
        "customerIpAddress": "127.0.0.1",
        "sourceObject": {
            "__typename": "Checkout",
            "id": checkout_id,
            "totalPrice": {"gross": {"amount": 0.0}},
            "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        },
    }


def test_transaction_initialize_session_checkout_without_data(
    checkout, webhook_app, permission_manage_payments, transaction_item_generator
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=TRANSACTION_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = None
    amount = Decimal(10)

    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        app=webhook_app,
        psp_reference=None,
        name=None,
        message=None,
    )
    action_type = TransactionFlowStrategy.CHARGE
    idempotency_key = str(uuid.uuid4())

    subscribable_object = TransactionSessionData(
        transaction=transaction,
        source_object=checkout,
        action=TransactionProcessActionData(
            amount=amount,
            currency=transaction.currency,
            action_type=action_type,
        ),
        customer_ip_address="127.0.0.1",
        payment_gateway_data=PaymentGatewayData(
            app_identifier=webhook_app.identifier, data=payload_data, error=None
        ),
        idempotency_key=idempotency_key,
    )

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, subscribable_object, [webhook]
    )[0]

    # then
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert delivery.payload
    assert delivery.payload.get_payload()
    assert json.loads(delivery.payload.get_payload()) == {
        "merchantReference": graphene.Node.to_global_id(
            "TransactionItem", transaction.token
        ),
        "action": {
            "amount": amount,
            "currency": "USD",
            "actionType": action_type.upper(),
        },
        "data": payload_data,
        "customerIpAddress": "127.0.0.1",
        "idempotencyKey": idempotency_key,
        "sourceObject": {
            "__typename": "Checkout",
            "id": checkout_id,
            "totalPrice": {"gross": {"amount": 0.0}},
            "user": None,
        },
    }


def test_transaction_initialize_session_order_with_data(
    order, webhook_app, permission_manage_payments, transaction_item_generator
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=TRANSACTION_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = {"some": "json data"}
    amount = Decimal(10)

    transaction = transaction_item_generator(
        order_id=order.pk,
        app=webhook_app,
        psp_reference=None,
        name=None,
        message=None,
    )
    action_type = TransactionFlowStrategy.CHARGE
    idempotency_key = str(uuid.uuid4())

    subscribable_object = TransactionSessionData(
        transaction=transaction,
        source_object=order,
        action=TransactionProcessActionData(
            amount=amount,
            currency=transaction.currency,
            action_type=action_type,
        ),
        customer_ip_address="127.0.0.1",
        payment_gateway_data=PaymentGatewayData(
            app_identifier=webhook_app.identifier, data=payload_data, error=None
        ),
        idempotency_key=idempotency_key,
    )

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, subscribable_object, [webhook]
    )[0]

    # then

    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert delivery.payload
    assert delivery.payload.get_payload()
    assert json.loads(delivery.payload.get_payload()) == {
        "merchantReference": graphene.Node.to_global_id(
            "TransactionItem", transaction.token
        ),
        "action": {
            "amount": amount,
            "currency": "USD",
            "actionType": action_type.upper(),
        },
        "idempotencyKey": idempotency_key,
        "data": payload_data,
        "customerIpAddress": "127.0.0.1",
        "sourceObject": {
            "__typename": "Order",
            "id": order_id,
            "user": {"id": graphene.Node.to_global_id("User", order.user.pk)},
        },
    }


def test_transaction_initialize_session_order_without_data(
    order, webhook_app, permission_manage_payments, transaction_item_generator
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=TRANSACTION_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = None
    amount = Decimal(10)

    transaction = transaction_item_generator(
        order_id=order.pk,
        app=webhook_app,
        psp_reference=None,
        name=None,
        message=None,
    )
    action_type = TransactionFlowStrategy.CHARGE
    idempotency_key = str(uuid.uuid4())

    subscribable_object = TransactionSessionData(
        transaction=transaction,
        source_object=order,
        action=TransactionProcessActionData(
            amount=amount,
            currency=transaction.currency,
            action_type=action_type,
        ),
        customer_ip_address="127.0.0.1",
        payment_gateway_data=PaymentGatewayData(
            app_identifier=webhook_app.identifier, data=payload_data, error=None
        ),
        idempotency_key=idempotency_key,
    )

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, subscribable_object, [webhook]
    )[0]

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert delivery.payload
    assert delivery.payload.get_payload()
    assert json.loads(delivery.payload.get_payload()) == {
        "merchantReference": graphene.Node.to_global_id(
            "TransactionItem", transaction.token
        ),
        "action": {
            "amount": amount,
            "currency": "USD",
            "actionType": action_type.upper(),
        },
        "idempotencyKey": idempotency_key,
        "data": payload_data,
        "customerIpAddress": "127.0.0.1",
        "sourceObject": {
            "__typename": "Order",
            "id": order_id,
            "user": {"id": graphene.Node.to_global_id("User", order.user.pk)},
        },
    }


def test_transaction_initialize_session_empty_customer_ip_addess(
    order, webhook_app, permission_manage_payments, transaction_item_generator
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=TRANSACTION_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)
    payload_data = None
    amount = Decimal(10)

    transaction = transaction_item_generator(
        order_id=order.pk,
        app=webhook_app,
        psp_reference=None,
        name=None,
        message=None,
    )
    action_type = TransactionFlowStrategy.CHARGE
    idempotency_key = str(uuid.uuid4())

    subscribable_object = TransactionSessionData(
        transaction=transaction,
        source_object=order,
        action=TransactionProcessActionData(
            amount=amount,
            currency=transaction.currency,
            action_type=action_type,
        ),
        customer_ip_address=None,
        payment_gateway_data=PaymentGatewayData(
            app_identifier=webhook_app.identifier, data=payload_data, error=None
        ),
        idempotency_key=idempotency_key,
    )

    # when
    delivery = create_deliveries_for_subscriptions(
        event_type, subscribable_object, [webhook]
    )[0]

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert delivery.payload
    assert delivery.payload.get_payload()
    assert json.loads(delivery.payload.get_payload()) == {
        "merchantReference": graphene.Node.to_global_id(
            "TransactionItem", transaction.token
        ),
        "action": {
            "amount": amount,
            "currency": "USD",
            "actionType": action_type.upper(),
        },
        "data": payload_data,
        "customerIpAddress": None,
        "idempotencyKey": idempotency_key,
        "sourceObject": {
            "__typename": "Order",
            "id": order_id,
            "user": {"id": graphene.Node.to_global_id("User", order.user.pk)},
        },
    }
