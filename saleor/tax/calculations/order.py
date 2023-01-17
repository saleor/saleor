from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Tuple

from prices import Money, TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import zero_money, zero_taxed_money
from ...discount import OrderDiscountType
from ...order import base_calculations
from ...order.utils import (
    get_order_country,
    get_total_order_discount_excluding_shipping,
)
from ..models import TaxClassCountryRate
from ..utils import (
    denormalize_tax_rate_from_db,
    get_tax_rate_for_tax_class,
    normalize_tax_rate_for_db,
)
from . import calculate_flat_rate_tax

if TYPE_CHECKING:
    from ...order.models import Order, OrderLine


def update_order_prices_with_flat_rates(
    order: "Order",
    lines: Iterable["OrderLine"],
    prices_entered_with_tax: bool,
):
    country_code = get_order_country(order)
    default_country_rate_obj = TaxClassCountryRate.objects.filter(
        country=country_code, tax_class=None
    ).first()
    default_tax_rate = (
        default_country_rate_obj.rate if default_country_rate_obj else Decimal(0)
    )

    # Calculate order line totals.
    _, undiscounted_subtotal = update_taxes_for_order_lines(
        order, lines, country_code, default_tax_rate, prices_entered_with_tax
    )

    # Calculate order shipping.
    shipping_method = order.shipping_method
    shipping_tax_class = getattr(shipping_method, "tax_class", None)
    if shipping_tax_class:
        shipping_tax_rate = get_tax_rate_for_tax_class(
            shipping_tax_class,
            shipping_tax_class.country_rates.all(),
            default_tax_rate,
            country_code,
        )
    elif order.shipping_tax_rate is not None:
        # Use order.shipping_tax_rate if it was ever set before (it's non-null now).
        # This is a valid case when recalculating shipping price and the tax class is
        # null, because it was removed from the system.
        shipping_tax_rate = denormalize_tax_rate_from_db(order.shipping_tax_rate)
    else:
        shipping_tax_rate = default_tax_rate

    order.shipping_price = _calculate_order_shipping(
        order, shipping_tax_rate, prices_entered_with_tax
    )
    order.shipping_tax_rate = normalize_tax_rate_for_db(shipping_tax_rate)

    # Calculate order total.
    order.undiscounted_total = undiscounted_subtotal + order.base_shipping_price
    order.total = _calculate_order_total(order, lines)


def _calculate_order_total(
    order: "Order",
    lines: Iterable["OrderLine"],
) -> TaxedMoney:
    currency = order.currency

    default_value = base_calculations.base_order_total(order, lines)
    default_value = TaxedMoney(default_value, default_value)
    if default_value <= zero_taxed_money(currency):
        return quantize_price(default_value, currency)

    total = zero_taxed_money(currency)
    undiscounted_subtotal = zero_taxed_money(currency)
    for line in lines:
        total += line.total_price
        undiscounted_subtotal += line.undiscounted_total_price
    total += order.shipping_price

    order_discount = order.discounts.filter(type=OrderDiscountType.MANUAL).first()
    if order_discount and order_discount.amount > undiscounted_subtotal.gross:
        remaining_amount = order_discount.amount - undiscounted_subtotal.gross
        total -= remaining_amount
    return quantize_price(max(total, zero_taxed_money(currency)), currency)


def _calculate_order_shipping(
    order: "Order", tax_rate: Decimal, prices_entered_with_tax: bool
) -> TaxedMoney:
    shipping_price = order.base_shipping_price
    taxed_shipping_price = calculate_flat_rate_tax(
        shipping_price, tax_rate, prices_entered_with_tax
    )
    return quantize_price(taxed_shipping_price, taxed_shipping_price.currency)


def update_taxes_for_order_lines(
    order: "Order",
    lines: Iterable["OrderLine"],
    country_code: str,
    default_tax_rate: Decimal,
    prices_entered_with_tax: bool,
) -> Tuple[Iterable["OrderLine"], TaxedMoney]:
    currency = order.currency
    lines = list(lines)

    total_discount_amount = get_total_order_discount_excluding_shipping(order).amount
    order_total_price = sum(
        [line.base_unit_price.amount * line.quantity for line in lines]
    )
    total_line_discounts = 0

    undiscounted_subtotal = zero_taxed_money(order.currency)

    for line in lines:
        variant = line.variant
        if not variant:
            continue

        tax_class = line.tax_class
        if tax_class:
            tax_rate = get_tax_rate_for_tax_class(
                tax_class,
                tax_class.country_rates.all() if tax_class else [],
                default_tax_rate,
                country_code,
            )
        elif line.tax_rate is not None:
            # line.tax_class can be None when the tax class was removed from DB. In
            # this case try to use line.tax_rate which stores the denormalized tax rate
            # value that was originally used.
            tax_rate = denormalize_tax_rate_from_db(line.tax_rate)
        else:
            tax_rate = default_tax_rate

        line_total_price = line.base_unit_price * line.quantity
        undiscounted_subtotal += line_total_price

        price_with_discounts = line.base_unit_price
        if total_discount_amount:
            if line is lines[-1]:
                # for the last line applied remaining discount
                discount_amount = total_discount_amount - total_line_discounts
            else:
                # calculate discount proportionally to the rate of total line price
                # to order total price.
                discount_amount = quantize_price(
                    line_total_price.amount / order_total_price * total_discount_amount,
                    currency,
                )
            price_with_discounts = max(
                quantize_price(
                    (line_total_price - Money(discount_amount, currency))
                    / line.quantity,
                    currency,
                ),
                zero_money(currency),
            )
            # sum already applied discounts
            total_line_discounts += discount_amount

        unit_price = calculate_flat_rate_tax(
            price_with_discounts, tax_rate, prices_entered_with_tax
        )
        undiscounted_unit_price = calculate_flat_rate_tax(
            line.undiscounted_base_unit_price, tax_rate, prices_entered_with_tax
        )

        line.unit_price = quantize_price(unit_price, currency)
        line.undiscounted_unit_price = quantize_price(undiscounted_unit_price, currency)

        line.total_price = quantize_price(unit_price * line.quantity, currency)
        line.undiscounted_total_price = quantize_price(
            undiscounted_unit_price * line.quantity, currency
        )
        line.tax_rate = normalize_tax_rate_for_db(tax_rate)

    return lines, undiscounted_subtotal
