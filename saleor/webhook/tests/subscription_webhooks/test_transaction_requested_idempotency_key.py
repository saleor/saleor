import json
from decimal import Decimal

import pytest

from ....graphql.payment.mutations.transaction.utils import (
    create_transaction_event_requested,
)
from ....payment import TransactionAction, TransactionEventType
from ....payment.interface import TransactionActionData
from ....payment.models import TransactionItem
from ...event_types import WebhookEventSyncType
from ...models import Webhook
from ...transport.asynchronous import create_deliveries_for_subscriptions

IDEMPOTENCY_KEY_SUBSCRIPTION = """
subscription {
  event {
    ... on TransactionChargeRequested {
      idempotencyKey
    }
    ... on TransactionRefundRequested {
      idempotencyKey
    }
    ... on TransactionCancelationRequested {
      idempotencyKey
    }
  }
}
"""


@pytest.mark.parametrize(
    ("_case", "event_type", "action_type", "request_event_type"),
    [
        (
            "charge",
            WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
            TransactionAction.CHARGE,
            TransactionEventType.CHARGE_REQUEST,
        ),
        (
            "refund",
            WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
            TransactionAction.REFUND,
            TransactionEventType.REFUND_REQUEST,
        ),
        (
            "cancelation",
            WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED,
            TransactionAction.CANCEL,
            TransactionEventType.CANCEL_REQUEST,
        ),
    ],
)
def test_payload_exposes_request_event_idempotency_key(
    _case,
    event_type,
    action_type,
    request_event_type,
    order,
    webhook_app,
    permission_manage_payments,
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "refund", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal(10),
        charged_value=Decimal(10),
    )
    action_value = Decimal("5.00")
    idempotency_key = "5b9a6d2e-2a0f-4f4f-9a3c-2f6d9e1b7c4a"
    request_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=request_event_type,
        idempotency_key=idempotency_key,
    )

    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=IDEMPOTENCY_KEY_SUBSCRIPTION,
    )
    webhook.events.create(event_type=event_type)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type=action_type,
        action_value=action_value,
        event=request_event,
        transaction_app_owner=None,
    )

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, transaction_data, [webhook]
    )

    # then
    assert len(deliveries) == 1
    assert json.loads(deliveries[0].payload.get_payload()) == {
        "idempotencyKey": request_event.idempotency_key
    }


@pytest.mark.parametrize(
    "action",
    [TransactionAction.CHARGE, TransactionAction.REFUND, TransactionAction.CANCEL],
)
def test_requested_event_is_always_created_with_an_idempotency_key(action, order):
    """Back the `idempotencyKey: String!` non-null guarantee at the mint site."""
    # given
    transaction = TransactionItem.objects.create(
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal(10),
        charged_value=Decimal(10),
    )

    # when
    request_event = create_transaction_event_requested(
        transaction, Decimal("5.00"), action
    )

    # then
    assert request_event.idempotency_key
