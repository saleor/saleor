import json
from decimal import Decimal

import graphene
from django.utils import timezone
from freezegun import freeze_time

from ....core.prices import quantize_price
from ....graphql.tests.queries import fragments
from ....payment import TransactionAction, TransactionEventType
from ....payment.interface import TransactionActionData
from ....payment.models import TransactionItem
from ...event_types import WebhookEventSyncType
from ...models import Webhook
from ...transport.asynchronous.transport import create_deliveries_for_subscriptions

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
        currency
      }
    }
  }
}
"""
)
TRANSACTION_REFUND_REQUESTED_WITH_GRANTED_REFUND_SUBSCRIPTION = (
    fragments.TRANSACTION_ITEM_DETAILS
    + """
subscription {
  event {
    ... on TransactionRefundRequested {
      transaction {
        ...TransactionFragment
      }
      grantedRefund{
        id
        amount{
          amount
        }
        lines{
          id
          quantity
          orderLine{
            unitPrice{
              gross{
                amount
              }
            }
          }
        }
      }
      action {
        actionType
        amount
        currency
      }
    }
  }
}
"""
)


@freeze_time("2020-03-18 12:00:00")
def test_order_transaction_refund_request(
    order, webhook_app, permission_manage_payments
):
    # given
    charged_value = Decimal(10)
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
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
    assert json.loads(deliveries[0].payload.get_payload()) == {
        "transaction": {
            "id": transaction_id,
            "createdAt": "2020-03-18T12:00:00+00:00",
            "actions": ["REFUND"],
            "authorizedAmount": {"currency": "USD", "amount": 0.0},
            "refundedAmount": {"currency": "USD", "amount": 0.0},
            "canceledAmount": {"currency": "USD", "amount": 0.0},
            "chargedAmount": {
                "currency": "USD",
                "amount": quantize_price(charged_value, "USD"),
            },
            "events": [
                {"id": graphene.Node.to_global_id("TransactionEvent", request_event.id)}
            ],
            "pspReference": "PSP ref",
            "order": {
                "id": graphene.Node.to_global_id("Order", order.id),
            },
            "checkout": None,
        },
        "action": {
            "actionType": "REFUND",
            "amount": quantize_price(action_value, "USD"),
            "currency": order.currency,
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_transaction_refund_request(
    checkout_with_items, webhook_app, permission_manage_payments
):
    # given
    checkout_with_items.price_expiration = timezone.now() - timezone.timedelta(hours=10)
    checkout_with_items.save()
    charged_value = Decimal(10)
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout_with_items.pk,
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
    checkout_with_items.refresh_from_db()
    assert json.loads(deliveries[0].payload.get_payload()) == {
        "transaction": {
            "id": transaction_id,
            "createdAt": "2020-03-18T12:00:00+00:00",
            "actions": ["REFUND"],
            "authorizedAmount": {"currency": "USD", "amount": 0.0},
            "refundedAmount": {"currency": "USD", "amount": 0.0},
            "canceledAmount": {"currency": "USD", "amount": 0.0},
            "chargedAmount": {
                "currency": "USD",
                "amount": quantize_price(charged_value, "USD"),
            },
            "events": [
                {"id": graphene.Node.to_global_id("TransactionEvent", request_event.id)}
            ],
            "pspReference": "PSP ref",
            "order": None,
            "checkout": {
                "channel": {
                    "slug": checkout_with_items.channel.slug,
                },
                "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
                "totalPrice": {
                    "gross": {
                        "amount": quantize_price(
                            checkout_with_items.total_gross_amount, "USD"
                        )
                    }
                },
            },
        },
        "action": {
            "actionType": "REFUND",
            "amount": quantize_price(action_value, "USD"),
            "currency": "USD",
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_transaction_refund_request_with_granted_refund(
    order_with_lines, webhook_app, permission_manage_payments
):
    # given
    charged_value = Decimal(10)
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order_with_lines.pk,
        charged_value=charged_value,
    )

    order_line = order_with_lines.lines.first()
    expected_amount = order_line.unit_price_gross_amount

    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=expected_amount
    )
    granted_refund_line = granted_refund.lines.create(
        quantity=1,
        order_line=order_line,
    )

    action_value = expected_amount
    request_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
    )

    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=(
            TRANSACTION_REFUND_REQUESTED_WITH_GRANTED_REFUND_SUBSCRIPTION
        ),
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
        granted_refund=granted_refund,
    )
    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, transaction_data, [webhook]
    )

    # then
    assert json.loads(deliveries[0].payload.get_payload()) == {
        "transaction": {
            "id": transaction_id,
            "createdAt": "2020-03-18T12:00:00+00:00",
            "actions": ["REFUND"],
            "authorizedAmount": {"currency": "USD", "amount": 0.0},
            "refundedAmount": {"currency": "USD", "amount": 0.0},
            "canceledAmount": {"amount": 0.0, "currency": "USD"},
            "chargedAmount": {
                "currency": "USD",
                "amount": quantize_price(charged_value, "USD"),
            },
            "events": [
                {"id": graphene.Node.to_global_id("TransactionEvent", request_event.id)}
            ],
            "pspReference": "PSP ref",
            "order": {"id": graphene.Node.to_global_id("Order", order_with_lines.id)},
            "checkout": None,
        },
        "grantedRefund": {
            "amount": {"amount": 12.3},
            "id": graphene.Node.to_global_id("OrderGrantedRefund", granted_refund.id),
            "lines": [
                {
                    "id": graphene.Node.to_global_id(
                        "OrderGrantedRefundLine", granted_refund_line.id
                    ),
                    "orderLine": {"unitPrice": {"gross": {"amount": 12.3}}},
                    "quantity": 1,
                }
            ],
        },
        "action": {
            "actionType": "REFUND",
            "amount": 12.3,
            "currency": "USD",
        },
    }
