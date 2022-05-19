import json
from decimal import Decimal

import graphene
from freezegun import freeze_time

from .....core.prices import quantize_price
from .....payment import TransactionAction
from .....payment.interface import TransactionActionData
from .....payment.models import TransactionItem
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook
from ...tasks import create_deliveries_for_subscriptions

TRANSACTION_ACTION_REQUEST_SUBSCRIPTION_QUERY = """
subscription{
  event{
    ... on TransactionActionRequest{
      transaction{
        id
        createdAt
        actions
        authorizedAmount{
          currency
          amount
        }
        refundedAmount{
          currency
          amount
        }
        voidedAmount{
          currency
          amount
        }
        chargedAmount{
          currency
          amount
        }
        events{
          id
        }
        status
        type
        reference
      }
      action{
        actionType
        amount
      }
    }
  }
}
"""


@freeze_time("2020-03-18 12:00:00")
def test_transaction_refund_action_request(
    order, webhook_app, permission_manage_payments
):
    # given
    charged_value = Decimal("10")
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        status="Captured",
        type="Credit card",
        reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        charged_value=charged_value,
    )
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TRANSACTION_ACTION_REQUEST_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST
    webhook.events.create(event_type=event_type)

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.id)
    action_value = Decimal("5.00")
    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.REFUND,
        action_value=action_value,
    )
    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, transaction_data, [webhook]
    )

    # then
    assert json.loads(deliveries[0].payload.payload) == {
        "transaction": {
            "id": transaction_id,
            "createdAt": "2020-03-18T12:00:00+00:00",
            "actions": ["REFUND"],
            "authorizedAmount": {"currency": "USD", "amount": 0.0},
            "refundedAmount": {"currency": "USD", "amount": 0.0},
            "voidedAmount": {"currency": "USD", "amount": 0.0},
            "chargedAmount": {
                "currency": "USD",
                "amount": quantize_price(charged_value, "USD"),
            },
            "events": [],
            "status": "Captured",
            "type": "Credit card",
            "reference": "PSP ref",
        },
        "action": {
            "actionType": "REFUND",
            "amount": quantize_price(action_value, "USD"),
        },
        "meta": None,
    }


@freeze_time("2020-03-18 12:00:00")
def test_transaction_charge_action_request(
    order, webhook_app, permission_manage_payments
):
    # given
    authorized_value = Decimal("10")
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["charge"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorized_value,
    )
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TRANSACTION_ACTION_REQUEST_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST
    webhook.events.create(event_type=event_type)

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.id)
    action_value = Decimal("5.00")
    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.CHARGE,
        action_value=action_value,
    )
    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, transaction_data, [webhook]
    )

    # then
    assert json.loads(deliveries[0].payload.payload) == {
        "transaction": {
            "id": transaction_id,
            "createdAt": "2020-03-18T12:00:00+00:00",
            "actions": ["CHARGE"],
            "authorizedAmount": {
                "currency": "USD",
                "amount": quantize_price(authorized_value, "USD"),
            },
            "refundedAmount": {"currency": "USD", "amount": 0.0},
            "voidedAmount": {"currency": "USD", "amount": 0.0},
            "chargedAmount": {"currency": "USD", "amount": 0.0},
            "events": [],
            "status": "Authorized",
            "type": "Credit card",
            "reference": "PSP ref",
        },
        "action": {
            "actionType": "CHARGE",
            "amount": quantize_price(action_value, "USD"),
        },
        "meta": None,
    }


@freeze_time("2020-03-18 12:00:00")
def test_transaction_void_action_request(
    order, webhook_app, permission_manage_payments
):
    # given
    authorized_value = Decimal("10")
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        status="Captured",
        type="Credit card",
        reference="PSP ref",
        available_actions=["void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorized_value,
    )
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TRANSACTION_ACTION_REQUEST_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST
    webhook.events.create(event_type=event_type)

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.id)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.VOID,
    )
    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, transaction_data, [webhook]
    )

    # then
    assert json.loads(deliveries[0].payload.payload) == {
        "transaction": {
            "id": transaction_id,
            "createdAt": "2020-03-18T12:00:00+00:00",
            "actions": ["VOID"],
            "authorizedAmount": {
                "currency": "USD",
                "amount": quantize_price(authorized_value, "USD"),
            },
            "refundedAmount": {"currency": "USD", "amount": 0.0},
            "voidedAmount": {"currency": "USD", "amount": 0.0},
            "chargedAmount": {"currency": "USD", "amount": 0.0},
            "events": [],
            "status": "Captured",
            "type": "Credit card",
            "reference": "PSP ref",
        },
        "action": {"actionType": "VOID", "amount": None},
        "meta": None,
    }
