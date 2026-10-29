import pytest

from ...core.exceptions import GiftCardNotApplicable
from ..checkout_cleaner import _validate_gift_cards


def test_validate_gift_cards_rejects_mismatched_assignment(
    checkout_with_gift_card, customer_user, staff_user
):
    # given
    checkout = checkout_with_gift_card
    checkout.user = staff_user
    checkout.save(update_fields=["user"])
    gift_card = checkout.gift_cards.first()
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])

    # when / then
    with pytest.raises(GiftCardNotApplicable):
        _validate_gift_cards(checkout)


def test_validate_gift_cards_allows_matching_assignment(
    checkout_with_gift_card, customer_user
):
    # given
    checkout = checkout_with_gift_card
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    gift_card = checkout.gift_cards.first()
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])

    # when / then (no raise)
    _validate_gift_cards(checkout)
