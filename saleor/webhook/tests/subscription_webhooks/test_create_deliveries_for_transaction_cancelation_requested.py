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
from ...transport.asynchronous import create_deliveries_for_subscriptions

TRANSACTION_CANCELATION_REQUESTED_SUBSCRIPTION = (
    fragments.TRANSACTION_ITEM_DETAILS
    + """
subscription {
  event {
    ... on TransactionCancelationRequested {
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


@freeze_time("2020-03-18 12:00:00")
def test_order_transaction_cancel_request(
    order, webhook_app, permission_manage_payments
):
    # given
    authorized_value = Decimal("10")
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorized_value,
    )

    request_event = transaction.events.create(
        currency=transaction.currency,
        type=TransactionEventType.CANCEL_REQUEST,
    )

    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TRANSACTION_CANCELATION_REQUESTED_SUBSCRIPTION,
    )
    event_type = WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    webhook.events.create(event_type=event_type)

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.CANCEL,
        event=request_event,
        transaction_app_owner=None,
        action_value=authorized_value,
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
            "actions": ["CANCEL"],
            "authorizedAmount": {
                "currency": "USD",
                "amount": quantize_price(authorized_value, "USD"),
            },
            "refundedAmount": {"currency": "USD", "amount": 0.0},
            "canceledAmount": {"currency": "USD", "amount": 0.0},
            "chargedAmount": {"currency": "USD", "amount": 0.0},
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
            "actionType": "CANCEL",
            "amount": quantize_price(authorized_value, "USD"),
            "currency": order.currency,
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_transaction_cancel_request(
    checkout_with_items, webhook_app, permission_manage_payments
):
    # given
    checkout_with_items.price_expiration = timezone.now() - timezone.timedelta(hours=10)
    checkout_with_items.save()
    authorized_value = Decimal("10")
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["cancel"],
        currency="USD",
        checkout_id=checkout_with_items.pk,
        authorized_value=authorized_value,
    )

    request_event = transaction.events.create(
        currency=transaction.currency,
        type=TransactionEventType.CANCEL_REQUEST,
    )

    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TRANSACTION_CANCELATION_REQUESTED_SUBSCRIPTION,
    )
    event_type = WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    webhook.events.create(event_type=event_type)

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type=TransactionAction.CANCEL,
        event=request_event,
        transaction_app_owner=None,
        action_value=authorized_value,
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
            "actions": ["CANCEL"],
            "authorizedAmount": {
                "currency": "USD",
                "amount": quantize_price(authorized_value, "USD"),
            },
            "refundedAmount": {"currency": "USD", "amount": 0.0},
            "canceledAmount": {"currency": "USD", "amount": 0.0},
            "chargedAmount": {"currency": "USD", "amount": 0.0},
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
            "actionType": "CANCEL",
            "amount": quantize_price(authorized_value, "USD"),
            "currency": "USD",
        },
    }
