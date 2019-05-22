import uuid

from ...discount.models import Voucher
from ...giftcard.models import GiftCard


def generate_promo_code(length=12):
    """Generate new unique gift card code."""
    code = str(uuid.uuid4()).replace("-", "").upper()[:length]
    while not is_avaible_promo_code(code):
        code = str(uuid.uuid4()).replace("-", "").upper()[:length]
    return code


def is_avaible_promo_code(code):
    return not (
        GiftCard.objects.filter(code=code).exists()
        or Voucher.objects.filter(code=code).exists()
    )
