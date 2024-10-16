from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from typing import Optional, TypeVar

from prices import Money, TaxedMoney, fixed_discount, percentage_discount

from ...core.prices import quantize_price
from ...core.taxes import zero_money
from .. import DiscountValueType
from ..models import OrderDiscount

T = TypeVar("T", Money, TaxedMoney)


def apply_discount_to_value(
    value: Decimal,
    value_type: Optional[str],
    currency: str,
    price_to_discount: T,
) -> T:
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


def split_manual_discount(
    discount: OrderDiscount, subtotal: Money, shipping_price: Money
) -> tuple[Money, Money]:
    """Discounts sent to tax app must be split into subtotal and shipping portion."""
    currency = subtotal.currency
    subtotal_discount, shipping_discount = zero_money(currency), zero_money(currency)
    total = subtotal + shipping_price
    if total.amount > 0:
        discounted_total = apply_discount_to_value(
            value=discount.value,
            value_type=discount.value_type,
            currency=currency,
            price_to_discount=total,
        )
        total_discount = total - discounted_total
        subtotal_discount = subtotal / total * total_discount
        shipping_discount = total_discount - subtotal_discount

    return quantize_price(subtotal_discount, currency), quantize_price(
        shipping_discount, currency
    )
