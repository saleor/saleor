from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from typing import Optional, Union

from prices import Money, TaxedMoney, fixed_discount, percentage_discount

from .. import DiscountValueType


def apply_discount_to_value(
    value: Decimal,
    value_type: Optional[str],
    currency: str,
    price_to_discount: Union[Money, TaxedMoney],
):
    """Calculate the price based on the provided values."""
    if value_type == DiscountValueType.PERCENTAGE:
        discount_method = percentage_discount
        discount_kwargs = {"percentage": value, "rounding": ROUND_HALF_UP}
    else:
        discount_method = fixed_discount
        discount_kwargs = {"discount": Money(value, currency)}
    discount = partial(
        discount_method,
        **discount_kwargs,
    )
    return discount(price_to_discount)
