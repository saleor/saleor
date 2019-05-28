from django.core.exceptions import ValidationError

from .models import GiftCard


def add_gift_card_code_to_checkout(checkout, promo_code):
    try:
        gift_card = GiftCard.objects.get(code=promo_code)
    except GiftCard.DoesNotExist:
        raise ValidationError({"promo_code": "Gift card with given code is invalid."})
    add_gift_card_to_checkout(checkout, gift_card)


def add_gift_card_to_checkout(checkout, gift_card):
    checkout.gift_cards.add(gift_card)
