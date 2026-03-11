from decimal import Decimal

import pytest

from ...giftcard import GiftCardEvents
from ...giftcard.const import GIFT_CARD_PAYMENT_GATEWAY_ID
from ...giftcard.gateway import (
    charge_gift_card_transactions,
    refund_gift_card_transaction,
)
from ...giftcard.models import GiftCardEvent
from ...payment import TransactionAction, TransactionEventType
from ...payment.models import TransactionEvent


@pytest.mark.django_db
def test_charge_creates_used_in_order_event(
    order, gift_card_created_by_staff, transaction_item_generator
):
    # given
    authorized_amount = Decimal("5.00")
    gift_card = gift_card_created_by_staff
    initial_balance = gift_card.current_balance_amount

    transaction_item_generator(
        order_id=order.pk,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        authorized_value=authorized_amount,
        charged_value=Decimal(0),
        gift_card=gift_card,
        available_actions=[TransactionAction.CHARGE],
    )

    # when
    charge_gift_card_transactions(order)

    # then
    gift_card.refresh_from_db()
    assert gift_card.current_balance_amount == initial_balance - authorized_amount
    assert gift_card.used_by == order.user
    assert gift_card.used_by_email == order.user_email
    assert gift_card.last_used_on is not None

    event = GiftCardEvent.objects.get(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )
    assert event.order == order
    assert event.parameters["balance"]["currency"] == gift_card.currency
    assert Decimal(event.parameters["balance"]["current_balance"]) == (
        initial_balance - authorized_amount
    )
    assert (
        Decimal(event.parameters["balance"]["old_current_balance"]) == initial_balance
    )


@pytest.mark.django_db
def test_charge_does_not_create_event_on_insufficient_funds(
    order, gift_card_created_by_staff, transaction_item_generator
):
    # given
    gift_card = gift_card_created_by_staff
    authorized_amount = gift_card.current_balance_amount + Decimal("1.00")

    transaction_item_generator(
        order_id=order.pk,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        authorized_value=authorized_amount,
        charged_value=Decimal(0),
        gift_card=gift_card,
        available_actions=[TransactionAction.CHARGE],
    )

    # when
    charge_gift_card_transactions(order)

    # then
    assert not GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    ).exists()


@pytest.mark.django_db
def test_refund_creates_refunded_in_order_event(
    order, gift_card_created_by_staff, transaction_item_generator
):
    # given
    charged_amount = Decimal("5.00")
    gift_card = gift_card_created_by_staff
    gift_card.current_balance_amount -= charged_amount
    gift_card.save(update_fields=["current_balance_amount"])
    balance_before_refund = gift_card.current_balance_amount

    transaction = transaction_item_generator(
        order_id=order.pk,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        authorized_value=Decimal(0),
        charged_value=charged_amount,
        gift_card=gift_card,
        available_actions=[TransactionAction.REFUND],
    )

    request_event = TransactionEvent.objects.create(
        transaction=transaction,
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=charged_amount,
        currency=transaction.currency,
        psp_reference="ref-1",
    )

    # when
    refund_gift_card_transaction(transaction, request_event)

    # then
    gift_card.refresh_from_db()
    assert gift_card.current_balance_amount == balance_before_refund + charged_amount

    event = GiftCardEvent.objects.get(
        gift_card=gift_card, type=GiftCardEvents.REFUNDED_IN_ORDER
    )
    assert event.order == order
    assert event.parameters["balance"]["currency"] == gift_card.currency
    assert Decimal(event.parameters["balance"]["current_balance"]) == (
        balance_before_refund + charged_amount
    )
    assert Decimal(event.parameters["balance"]["old_current_balance"]) == (
        balance_before_refund
    )
