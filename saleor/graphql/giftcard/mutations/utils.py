from django.core.exceptions import ValidationError

from ....giftcard import models
from ....giftcard.error_codes import GiftCardErrorCode
from ....giftcard.utils import is_gift_card_expired


def clean_gift_card(gift_card: models.GiftCard) -> models.GiftCard:
    if is_gift_card_expired(gift_card):
        raise ValidationError(
            {
                "id": ValidationError(
                    "Expired gift card cannot be activated and resend.",
                    code=GiftCardErrorCode.EXPIRED_GIFT_CARD.value,
                )
            }
        )
    return gift_card
