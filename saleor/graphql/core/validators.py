from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django_prices.utils.formatting import get_currency_fraction
from graphql.error import GraphQLError

if TYPE_CHECKING:
    from decimal import Decimal


def validate_one_of_args_is_in_query(arg1_name, arg1, arg2_name, arg2):
    if arg1 and arg2:
        raise GraphQLError(
            f"Argument '{arg1_name}' cannot be combined with '{arg2_name}'"
        )
    if not arg1 and not arg2:
        raise GraphQLError(
            f"Either '{arg1_name}'  or '{arg2_name}' argument is required"
        )


def validate_price_precision(value: Optional["Decimal"], currency: str = None):
    """Validate if price amount does not have too many decimal places.

    Price amount can't have more decimal places than currency allow to.
    Works only with decimal created from a string.
    """

    # check no needed when there is no value
    if not value:
        return

    currency_fraction = get_currency_fraction(currency or settings.DEFAULT_CURRENCY)
    value = value.normalize()
    if abs(value.as_tuple().exponent) > currency_fraction:
        raise ValidationError(
            f"Value cannot have more than {currency_fraction} decimal places."
        )
