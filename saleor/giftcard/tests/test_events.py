from decimal import Decimal

from .. import GiftCardEvents
from ..events import (
    gift_card_assigned_event,
    gift_card_balance_adjusted_event,
    gift_card_unassigned_event,
)


def test_gift_card_balance_adjusted_event(gift_card, staff_user):
    # given
    old_current = Decimal("50.00")
    old_initial = Decimal("100.00")

    # when
    event = gift_card_balance_adjusted_event(
        gift_card, old_current, old_initial, staff_user, None
    )

    # then
    assert event.type == GiftCardEvents.BALANCE_ADJUSTED
    balance = event.parameters["balance"]
    assert balance["old_current_balance"] == old_current
    assert balance["old_initial_balance"] == old_initial
    assert balance["current_balance"] == gift_card.current_balance_amount
    assert balance["initial_balance"] == gift_card.initial_balance_amount
    assert balance["currency"] == gift_card.currency


def test_gift_card_assigned_event_records_prev_and_new(
    gift_card, customer_user, staff_user
):
    # given
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email

    # when
    event = gift_card_assigned_event(gift_card, None, None, staff_user, None)

    # then
    assert event.type == GiftCardEvents.ASSIGNED_TO_USER
    assert event.parameters["previous_assigned_to_id"] is None
    assert event.parameters["previous_assigned_to_email"] is None
    assert event.parameters["assigned_to_id"] == customer_user.id
    assert event.parameters["assigned_to_email"] == customer_user.email


def test_gift_card_unassigned_event_records_prev(gift_card, customer_user, staff_user):
    # when
    event = gift_card_unassigned_event(
        gift_card, customer_user.id, customer_user.email, staff_user, None
    )

    # then
    assert event.type == GiftCardEvents.UNASSIGNED_FROM_USER
    assert event.parameters["previous_assigned_to_id"] == customer_user.id
    assert event.parameters["previous_assigned_to_email"] == customer_user.email
