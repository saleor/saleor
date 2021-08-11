from datetime import date, timedelta

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from ...core.utils.promo_code import InvalidPromoCode
from ..utils import (
    add_gift_card_code_to_checkout,
    calculate_expiry_date,
    remove_gift_card_code_from_checkout,
)


def test_add_gift_card_code_to_checkout(checkout, gift_card):
    # given
    assert checkout.gift_cards.count() == 0

    # when
    add_gift_card_code_to_checkout(
        checkout, "test@example.com", gift_card.code, gift_card.currency
    )

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
        add_gift_card_code_to_checkout(
            checkout, "test@example.com", gift_card.code, gift_card.currency
        )


def test_add_gift_card_code_to_checkout_expired_card(checkout, gift_card):
    # given
    gift_card.expiry_date = date.today() - timedelta(days=10)
    gift_card.save(update_fields=["expiry_date"])

    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, "test@example.com", gift_card.code, gift_card.currency
        )


def test_add_gift_card_code_to_checkout_invalid_currency(checkout, gift_card):
    # given
    currency = "EUR"

    assert gift_card.currency != currency
    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, "test@example.com", gift_card.code, currency
        )


def test_add_gift_card_code_to_checkout_used_gift_card(checkout, gift_card_used):
    # given
    assert gift_card_used.used_by_email
    assert checkout.gift_cards.count() == 0

    # when
    add_gift_card_code_to_checkout(
        checkout,
        gift_card_used.used_by_email,
        gift_card_used.code,
        gift_card_used.currency,
    )

    # then
    assert checkout.gift_cards.count() == 1


def test_add_gift_card_code_to_checkout_used_gift_card_invalid_user(
    checkout, gift_card_used
):
    # given
    email = "new_user@example.com"
    assert gift_card_used.used_by_email
    assert gift_card_used.used_by_email != email
    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, email, gift_card_used.code, gift_card_used.currency
        )


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


@pytest.mark.parametrize(
    "period_type, period", [("years", 5), ("months", 13), ("days", 100)]
)
def test_calculate_expiry_settings(period_type, period, gift_card_expiry_period):
    # given
    gift_card_expiry_period.expiry_period_type = period_type.rstrip("s")
    gift_card_expiry_period.expiry_period = period
    gift_card_expiry_period.save(update_fields=["expiry_period_type", "expiry_period"])

    # when
    expiry_date = calculate_expiry_date(gift_card_expiry_period)

    # then
    assert expiry_date == timezone.now().date() + relativedelta(**{period_type: period})


def test_calculate_expiry_settings_for_never_expire_gift_card(gift_card):
    # when
    expiry_date = calculate_expiry_date(gift_card)

    # then
    assert expiry_date is None


def test_calculate_expiry_settings_for_expire_date_gift_card(gift_card_expiry_date):
    # when
    expiry_date = calculate_expiry_date(gift_card_expiry_date)

    # then
    assert expiry_date is None
