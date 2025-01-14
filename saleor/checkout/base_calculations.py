"""Contains functions which are base for calculating checkout properties.

It's recommended to use functions from calculations.py module to take in account
plugin manager. Functions from this module return price without
taxes (Money instead of TaxedMoney). If you don't need pre-taxed prices use functions
from calculations.py.
"""

from typing import TYPE_CHECKING

from prices import Money

from ..core.prices import quantize_price
from ..core.taxes import zero_money
from ..discount import VoucherType

if TYPE_CHECKING:
    from ..channel.models import Channel
    from .fetch import CheckoutInfo, CheckoutLineInfo, ShippingMethodInfo


def calculate_base_line_unit_price(
    line_info: "CheckoutLineInfo",
) -> Money:
    """Calculate line unit price including discounts and vouchers.

    The price includes catalogue promotions, specific product and applied once per order
    voucher discounts.
    The price does not include the entire order discount.
    """
    total_line_price = calculate_base_line_total_price(line_info=line_info)
    quantity = line_info.line.quantity
    currency = total_line_price.currency
    return quantize_price(total_line_price / quantity, currency)


def calculate_base_line_total_price(
    line_info: "CheckoutLineInfo",
    include_voucher: bool = True,
) -> Money:
    """Calculate line total price including discounts and vouchers.

    The price includes catalogue promotions, specific product and applied once per order
    voucher discounts.
    The price does not include order promotions and the entire order vouchers.
    When the line is gift reward, the price is zero.
    """
    from ..discount.utils.voucher import calculate_line_discount_amount_from_voucher

    variant_price = line_info.undiscounted_unit_price

    total_price = variant_price * line_info.line.quantity

    for discount in line_info.discounts:
        discount_amount = Money(discount.amount_value, line_info.line.currency)
        total_price -= discount_amount

    if include_voucher and line_info.voucher:
        discount_amount = calculate_line_discount_amount_from_voucher(
            line_info, total_price
        )
        total_price -= discount_amount

    return quantize_price(total_price, total_price.currency)


def calculate_undiscounted_base_line_total_price(
    line_info: "CheckoutLineInfo",
    channel: "Channel",
) -> Money:
    """Calculate line total price excluding discounts and vouchers."""
    unit_price = calculate_undiscounted_base_line_unit_price(
        line_info=line_info, channel=channel
    )
    total_price = unit_price * line_info.line.quantity
    return quantize_price(total_price, total_price.currency)


def calculate_undiscounted_base_line_unit_price(
    line_info: "CheckoutLineInfo",
    channel: "Channel",
):
    """Calculate line unit price without discounts and vouchers."""
    variant_price = line_info.undiscounted_unit_price
    return quantize_price(variant_price, variant_price.currency)


def base_checkout_delivery_price(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"] | None = None,
    include_voucher: bool = True,
) -> Money:
    """Calculate base (untaxed) price for any kind of delivery method."""
    currency = checkout_info.checkout.currency

    shipping_price = base_checkout_undiscounted_delivery_price(checkout_info, lines)

    is_shipping_voucher = (
        checkout_info.voucher.type == VoucherType.SHIPPING
        if include_voucher and checkout_info.voucher
        else False
    )

    if is_shipping_voucher:
        discount = checkout_info.checkout.discount
        shipping_price = max(zero_money(currency), shipping_price - discount)

    return quantize_price(
        shipping_price,
        currency,
    )


def base_checkout_undiscounted_delivery_price(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"] | None = None,
) -> Money:
    """Calculate base (untaxed) undiscounted price for any kind of delivery method."""
    from .fetch import ShippingMethodInfo

    delivery_method_info = checkout_info.delivery_method_info
    currency = checkout_info.checkout.currency

    if not isinstance(delivery_method_info, ShippingMethodInfo):
        return zero_money(currency)

    return calculate_base_price_for_shipping_method(
        checkout_info, delivery_method_info, lines
    )


def calculate_base_price_for_shipping_method(
    checkout_info: "CheckoutInfo",
    shipping_method_info: "ShippingMethodInfo",
    lines: list["CheckoutLineInfo"] | None = None,
) -> Money:
    """Return checkout shipping price."""
    from .fetch import CheckoutLineInfo

    shipping_method = shipping_method_info.delivery_method

    if lines is not None and all(isinstance(line, CheckoutLineInfo) for line in lines):
        from .utils import is_shipping_required

        shipping_required = is_shipping_required(lines)
    else:
        shipping_required = checkout_info.checkout.is_shipping_required()

    if not shipping_method or not shipping_required:
        return zero_money(checkout_info.checkout.currency)

    return quantize_price(
        shipping_method.price,
        checkout_info.checkout.currency,
    )


def base_checkout_total(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
) -> Money:
    """Return the total cost of the checkout.

    The price includes catalogue promotions, shipping, specific product
    and applied once per order voucher discounts.
    The price does not include order promotions and the entire order vouchers.
    """
    currency = checkout_info.checkout.currency
    subtotal = base_checkout_subtotal(lines, checkout_info.channel, currency)
    shipping_price = base_checkout_delivery_price(checkout_info, lines)

    return subtotal + shipping_price


def base_checkout_subtotal(
    checkout_lines: list["CheckoutLineInfo"],
    channel: "Channel",
    currency: str,
    include_voucher: bool = True,
) -> Money:
    """Return the checkout subtotal value.

    The price includes catalogue promotions, specific product and applied once per order
    voucher discounts.
    The price does not include order promotions and the entire order vouchers.
    """
    line_totals = [
        calculate_base_line_total_price(
            line,
            include_voucher=include_voucher,
        )
        for line in checkout_lines
    ]

    return sum(line_totals, zero_money(currency))


def checkout_total(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
) -> Money:
    """Return the total cost of the checkout including discounts and vouchers.

    It should be used as a based value when no flat rate/tax plugin/tax app is active.
    """
    from ..discount.utils.voucher import is_order_level_voucher

    currency = checkout_info.checkout.currency
    subtotal = base_checkout_subtotal(lines, checkout_info.channel, currency)
    shipping_price = base_checkout_delivery_price(checkout_info, lines)
    discount = checkout_info.checkout.discount

    # order promotion discount and entire_order voucher discount with
    # apply_once_per_order set to False are not included in the total price yet
    discounted_object_promotion = bool(checkout_info.discounts)
    discount_not_included = discounted_object_promotion or is_order_level_voucher(
        checkout_info.voucher
    )
    # Discount is subtracted from both gross and net values, which may cause negative
    # net value if we are having a discount that covers whole price.
    if discount_not_included:
        subtotal = max(zero_money(currency), subtotal - discount)
    return subtotal + shipping_price


def get_line_total_price_with_propagated_checkout_discount(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
) -> Money:
    """Calculate the checkout line price with discounts.

    Include the entire order voucher discount or discount from order
    promotion (this discount is applied only when voucher code is not set).
    The discount amount is calculated for every line proportionally to
    the rate of total line price to checkout total price.
    """
    voucher = checkout_info.voucher
    base_total_price = calculate_base_line_total_price(
        checkout_line_info,
    )
    if voucher and (
        voucher.apply_once_per_order
        or voucher.type in [VoucherType.SHIPPING, VoucherType.SPECIFIC_PRODUCT]
    ):
        return base_total_price

    if not voucher and not checkout_info.discounts:
        return base_total_price

    total_discount = checkout_info.checkout.discount
    for (
        checkout_line,
        total_price,
    ) in _propagate_checkout_discount_on_checkout_lines_prices(
        lines, total_discount, checkout_info.channel.currency_code
    ):
        if checkout_line_info.line.id == checkout_line.id:
            return total_price
    return base_total_price


def _propagate_checkout_discount_on_checkout_lines_prices(
    lines: list["CheckoutLineInfo"],
    total_discount: Money,
    currency: str,
):
    """Apply checkout discount on checkout line price.

    Propagate the discount amount proportionally to total prices of items.
    Ensure that the sum of discounts is equal to the discount amount.
    """
    lines = list(lines)
    lines_count = len(lines)

    # if the checkout has a single line, the whole discount amount will be applied
    # to this line
    if lines_count == 1:
        line_info = lines[0]
        line_total_price = calculate_base_line_total_price(line_info)
        yield (
            line_info.line,
            max(
                (line_total_price - total_discount),
                zero_money(currency),
            ),
        )
    elif lines_count > 1:
        # if the checkout has more lines we need to propagate the discount amount
        # proportionally to total prices of items
        lines_total_prices = [
            calculate_base_line_total_price(
                line_info,
            )
            for line_info in lines
        ]

        total_price = sum(lines_total_prices, start=Money(0, currency))
        remaining_discount = total_discount
        for idx, line_info in enumerate(lines):
            line = line_info.line
            if not total_price:
                yield line, zero_money(currency)
            elif idx < lines_count - 1:
                line_total_price = lines_total_prices[idx]
                share = line_total_price / total_price
                discount = quantize_price(
                    min(share * total_discount, line_total_price), currency
                )
                yield (
                    line,
                    max(
                        (line_total_price - discount),
                        zero_money(currency),
                    ),
                )
                remaining_discount -= discount
            else:
                line_total_price = lines_total_prices[idx]
                yield (
                    line,
                    max(
                        (line_total_price - remaining_discount),
                        zero_money(currency),
                    ),
                )
