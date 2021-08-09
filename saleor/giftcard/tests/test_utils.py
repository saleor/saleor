from datetime import date, timedelta

import pytest

from ...core.utils.promo_code import InvalidPromoCode
from ..utils import add_gift_card_code_to_checkout, remove_gift_card_code_from_checkout


def test_add_gift_card_code_to_checkout(checkout, gift_card):
    # given
    assert checkout.gift_cards.count() == 0

    # when
    add_gift_card_code_to_checkout(checkout, gift_card.code)

    # then
    assert checkout.gift_cards.count() == 1


def test_add_gift_card_code_to_checkout_inactive_card(checkout, gift_card):
    # given
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])

    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(checkout, gift_card.code)


def test_add_gift_card_code_to_checkout_expired_card(checkout, gift_card):
    # given
    gift_card.expiry_date = date.today() - timedelta(days=10)
    gift_card.save(update_fields=["expiry_date"])

    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(checkout, gift_card.code)


def test_remove_gift_card_code_from_checkout(checkout, gift_card):
    # given
    checkout.gift_cards.add(gift_card)
    assert checkout.gift_cards.count() == 1

    # when
    remove_gift_card_code_from_checkout(checkout, gift_card.code)

    # then
    assert checkout.gift_cards.count() == 0


def test_remove_gift_card_code_from_checkout_no_checkout_gift_cards(
    checkout, gift_card
):
    # given
    assert checkout.gift_cards.count() == 0

    # when
    remove_gift_card_code_from_checkout(checkout, gift_card.code)

    # then
    assert checkout.gift_cards.count() == 0
