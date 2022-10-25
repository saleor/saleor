from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional

from prices import Money, TaxedMoney

from ...checkout import base_calculations
from ...core.prices import quantize_price
from ...core.taxes import zero_money, zero_taxed_money
from ...discount import DiscountInfo, VoucherType
from ..models import TaxClassCountryRate
from ..utils import get_tax_rate_for_tax_class, normalize_tax_rate_for_db
from . import calculate_flat_rate_tax

if TYPE_CHECKING:
    from ...account.models import Address
    from ...channel.models import Channel
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...checkout.models import Checkout


def update_checkout_prices_with_flat_rates(
    checkout: "Checkout",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
    address: Optional["Address"] = None,
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    if not discounts:
        discounts = []

    country_code = (
        address.country.code if address else checkout_info.channel.default_country.code
    )
    default_country_rate_obj = TaxClassCountryRate.objects.filter(
        country=country_code, tax_class=None
    ).first()
    default_tax_rate = (
        default_country_rate_obj.rate if default_country_rate_obj else Decimal(0)
    )
    currency = checkout.currency

    # Calculate checkout line totals.
    for line_info in lines:
        line = line_info.line
        tax_class = line_info.tax_class
        tax_rate = get_tax_rate_for_tax_class(
            tax_class,
            tax_class.country_rates.all() if tax_class else [],
            default_tax_rate,
            country_code,
        )
        line_total_price = calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            discounts,
            tax_rate,
            prices_entered_with_tax,
        )
        line.total_price = line_total_price
        line.tax_rate = normalize_tax_rate_for_db(tax_rate)

    # Calculate shipping price.
    shipping_method = checkout_info.delivery_method_info.delivery_method
    tax_class = getattr(shipping_method, "tax_class", None)
    shipping_tax_rate = get_tax_rate_for_tax_class(
        tax_class,
        tax_class.country_rates.all() if tax_class else [],
        default_tax_rate,
        country_code,
    )
    shipping_price = calculate_checkout_shipping(
        checkout_info, lines, shipping_tax_rate, prices_entered_with_tax
    )
    checkout.shipping_price = shipping_price
    checkout.shipping_tax_rate = normalize_tax_rate_for_db(shipping_tax_rate)

    # Calculate subtotal and total.
    subtotal = sum(
        [line_info.line.total_price for line_info in lines], zero_taxed_money(currency)
    )
    checkout.subtotal = subtotal
    checkout.total = subtotal + shipping_price


def calculate_checkout_shipping(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    tax_rate: Decimal,
    prices_entered_with_tax: bool,
) -> TaxedMoney:
    shipping_price = base_calculations.base_checkout_delivery_price(
        checkout_info, lines
    )
    shipping_price_taxed = calculate_flat_rate_tax(
        shipping_price, tax_rate, prices_entered_with_tax
    )
    return quantize_price(shipping_price_taxed, shipping_price_taxed.currency)


def calculate_checkout_line_total(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable["DiscountInfo"],
    tax_rate: Decimal,
    prices_entered_with_tax: bool,
) -> TaxedMoney:
    unit_taxed_price = _calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_info.channel,
        discounts,
        tax_rate,
        prices_entered_with_tax,
    )
    quantity = checkout_line_info.line.quantity
    return quantize_price(unit_taxed_price * quantity, unit_taxed_price.currency)


def _calculate_checkout_line_unit_price(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    channel: "Channel",
    discounts: Iterable["DiscountInfo"],
    tax_rate: Decimal,
    prices_entered_with_tax: bool,
):
    unit_price = base_calculations.calculate_base_line_unit_price(
        checkout_line_info,
        channel,
        discounts,
    )
    unit_price = apply_checkout_discount_on_checkout_line(
        checkout_info,
        lines,
        checkout_line_info,
        discounts,
        unit_price,
    )
    return calculate_flat_rate_tax(unit_price, tax_rate, prices_entered_with_tax)


def apply_checkout_discount_on_checkout_line(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable["DiscountInfo"],
    line_price: Money,
):
    """Calculate the checkout line price with discounts.

    Include the entire order voucher discount.
    The discount amount is calculated for every line proportionally to
    the rate of total line price to checkout total price.
    """
    voucher = checkout_info.voucher
    if (
        not voucher
        or voucher.apply_once_per_order
        or voucher.type in [VoucherType.SHIPPING, VoucherType.SPECIFIC_PRODUCT]
    ):
        return line_price

    line_quantity = checkout_line_info.line.quantity
    total_discount_amount = checkout_info.checkout.discount_amount
    line_total_price = line_price * line_quantity
    currency = checkout_info.checkout.currency

    lines = list(lines)

    # if the checkout has a single line, the whole discount amount will be applied
    # to this line
    if len(lines) == 1:
        return max(
            (line_total_price - Money(total_discount_amount, currency)) / line_quantity,
            zero_money(currency),
        )

    # if the checkout has more lines we need to propagate the discount amount
    # proportionally to total prices of items
    lines_total_prices = [
        base_calculations.calculate_base_line_unit_price(
            line_info,
            checkout_info.channel,
            discounts,
        ).amount
        * line_info.line.quantity
        for line_info in lines
        if line_info.line.id != checkout_line_info.line.id
    ]

    total_price = sum(lines_total_prices) + line_total_price.amount

    last_element = lines[-1].line.id == checkout_line_info.line.id
    if last_element:
        discount_amount = _calculate_discount_for_last_element(
            lines_total_prices, total_price, total_discount_amount, currency
        )
    else:
        discount_amount = line_total_price.amount / total_price * total_discount_amount
    return max(
        (line_total_price - Money(discount_amount, currency)) / line_quantity,
        zero_money(currency),
    )


def _calculate_discount_for_last_element(
    lines_total_prices, total_price, total_discount_amount, currency
):
    """Calculate the discount for last element.

    If the given line is last on the list we should calculate the discount by difference
    between total discount amount and sum of discounts applied to rest of the lines,
    otherwise the sum of discounts won't be equal to the discount amount.
    """
    sum_of_discounts_other_elements = sum(
        [
            line_total_price / total_price * total_discount_amount
            for line_total_price in lines_total_prices
        ]
    )
    return total_discount_amount - sum_of_discounts_other_elements
