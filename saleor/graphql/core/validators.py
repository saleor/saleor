from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ValidationError
from django_prices.utils.formatting import get_currency_fraction
from graphql.error import GraphQLError

if TYPE_CHECKING:
    from decimal import Decimal


def validate_one_of_args_is_in_query(*args):
    # split args into a list with 2-element tuples:
    # [(arg1_name, arg1_value), (arg2_name, arg2_value), ...]
    splitted_args = [args[i : i + 2] for i in range(0, len(args), 2)]  # noqa: E203
    # filter trueish values from each tuple
    filter_args = list(filter(lambda item: bool(item[1]) is True, splitted_args))

    if len(filter_args) > 1:
        rest_args = ", ".join([f"'{item[0]}'" for item in filter_args[1:]])
        raise GraphQLError(
            f"Argument '{filter_args[0][0]}' cannot be combined with {rest_args}"
        )

    if not filter_args:
        required_args = ", ".join([f"'{item[0]}'" for item in splitted_args])
        raise GraphQLError(f"At least one of arguments is required: {required_args}.")


def validate_price_precision(value: Optional["Decimal"], currency: str):
    """Validate if price amount does not have too many decimal places.

    Price amount can't have more decimal places than currency allow to.
    Works only with decimal created from a string.
    """

    # check no needed when there is no value
    if not value:
        return
    currency_fraction = get_currency_fraction(currency)
    value = value.normalize()
    if value.as_tuple().exponent < -currency_fraction:
        raise ValidationError(
            f"Value cannot have more than {currency_fraction} decimal places."
        )
