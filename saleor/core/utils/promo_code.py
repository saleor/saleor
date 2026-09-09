import secrets

from django.core.exceptions import ValidationError

from ...discount.models import VoucherCode
from ...giftcard.error_codes import GiftCardErrorCode
from ...giftcard.models import GiftCard


class InvalidPromoCode(ValidationError):
    def __init__(self, message=None, promo_code_rejection=None, **kwargs):
        """Raise a generic invalid promo code error.

        `promo_code_rejection` carries a `PromoCodeRejection` describing why the
        code was rejected, for voucher and gift card codes alike.
        """
        self.rejection = promo_code_rejection
        if message is None:
            message = {
                "promo_code": ValidationError(
                    "Promo code is invalid",
                    code=GiftCardErrorCode.INVALID.value,
                    params=(
                        {"promo_code_details": promo_code_rejection}
                        if promo_code_rejection
                        else None
                    ),
                )
            }
        super().__init__(message, **kwargs)


def generate_promo_code():
    """Generate a promo unique code that can be used as a voucher or gift card code."""
    code = generate_random_code()
    while not is_available_promo_code(code):
        code = generate_random_code()
    return code


def generate_random_code():
    # generate code in format "ABCD-EFGH-IJKL"
    code = secrets.token_hex(nbytes=6).upper()
    return "-".join(code[i : i + 4] for i in range(0, len(code), 4))  # noqa: E203


def is_available_promo_code(code):
    return not (promo_code_is_gift_card(code) or promo_code_is_voucher(code))


def promo_code_is_voucher(code):
    return VoucherCode.objects.filter(code=code).exists()


def promo_code_is_gift_card(code):
    return GiftCard.objects.filter(code=code).exists()
