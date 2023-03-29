import json
from decimal import Decimal

import graphene
from freezegun import freeze_time

from .....core.prices import quantize_price
from .....graphql.tests.queries import fragments
from .....payment import TransactionAction, TransactionEventType
from .....payment.interface import TransactionActionData
from .....payment.models import TransactionItem
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.models import Webhook
from ...tasks import create_deliveries_for_subscriptions

TRANSACTION_REFUND_REQUESTED_SUBSCRIPTION = (
    fragments.TRANSACTION_ITEM_DETAILS
    + """
subscription {
  event {
    ... on TransactionRefundRequested {
      transaction {
        ...TransactionFragment
      }
      action {
        actionType
        amount
      }
    }
  }
}
"""
)


@freeze_time("2020-03-18 12:00:00")
def test_transaction_refund_request(order, webhook_app, permission_manage_payments):
    # given
    charged_value = Decimal("10")
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        status="Captured",
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        charged_value=charged_value,
    )

    action_value = Decimal("5.00")
    request_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
    )

    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TRANSACTION_REFUND_REQUESTED_SUBSCRIPTION,
    )
    event_type = WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    webhook.events.create(event_type=event_type)

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.REFUND,
        action_value=action_value,
        event=request_event,
        transaction_app_owner=None,
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
            "events": [
                {"id": graphene.Node.to_global_id("TransactionEvent", request_event.id)}
            ],
            "status": "Captured",
            "type": "Credit card",
            "reference": "PSP ref",
            "pspReference": "PSP ref",
            "order": {"id": graphene.Node.to_global_id("Order", order.id)},
        },
        "action": {
            "actionType": "REFUND",
            "amount": quantize_price(action_value, "USD"),
        },
    }
