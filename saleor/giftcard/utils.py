from datetime import date

from ..checkout.models import Checkout
from ..core.utils.promo_code import InvalidPromoCode
from .models import GiftCard


def add_gift_card_code_to_checkout(checkout: Checkout, promo_code: str):
    """Add gift card data to checkout by code.

    Raise InvalidPromoCode if gift card cannot be applied.
    """
    try:
        gift_card = GiftCard.objects.active(date=date.today()).get(code=promo_code)
    except GiftCard.DoesNotExist:
        raise InvalidPromoCode()
    checkout.gift_cards.add(gift_card)


def remove_gift_card_code_from_checkout(checkout: Checkout, gift_card_code: str):
    """Remove gift card data from checkout by code."""
    gift_card = checkout.gift_cards.filter(code=gift_card_code).first()
    if gift_card:
        checkout.gift_cards.remove(gift_card)


def deactivate_gift_card(gift_card: GiftCard):
    """Set gift card status as inactive."""
    if gift_card.is_active:
        gift_card.is_active = False
        gift_card.save(update_fields=["is_active"])


def activate_gift_card(gift_card: GiftCard):
    """Set gift card status as active."""
    if not gift_card.is_active:
        gift_card.is_active = True
        gift_card.save(update_fields=["is_active"])
