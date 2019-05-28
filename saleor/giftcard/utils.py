from datetime import date

from django.core.exceptions import ValidationError

from .models import GiftCard
from ..checkout.models import Checkout


def add_gift_card_code_to_checkout(checkout: Checkout, promo_code: str):
    """Add gift card data to checkout by code.

    Raise ValidationError if gift card cannot be applied."""
    try:
        gift_card = GiftCard.objects.active(date=date.today()).get(code=promo_code)
    except GiftCard.DoesNotExist:
        raise ValidationError({"promo_code": "Gift card with given code is invalid."})
    add_gift_card_to_checkout(checkout, gift_card)


def add_gift_card_to_checkout(checkout: Checkout, gift_card: str):
    """Add gift card data to checkout."""
    checkout.gift_cards.add(gift_card)


def remove_gift_card_code_from_checkout(checkout: Checkout, gift_card_code: str):
    """Remove voucher data from checkout by code"""
    gift_card = checkout.gift_cards.filter(code=gift_card_code).first()
    if gift_card:
        checkout.gift_cards.remove(gift_card)
