from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

from ....core.validators import validate_price_precision

if TYPE_CHECKING:
    from decimal import Decimal


def clean_fixed_discount_value(
    reward_value: "Decimal", error_code: str, currency_code: str
):
    try:
        validate_price_precision(reward_value, currency_code)
    except ValidationError:
        raise ValidationError(
            "Invalid amount precision.",
            code=error_code,
        )


def clean_percentage_discount_value(reward_value: "Decimal", error_code: str):
    if reward_value > 100:
        raise ValidationError(
            "Invalid percentage value.",
            code=error_code,
        )
