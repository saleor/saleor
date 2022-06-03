"""Contain functions which are base for calculating checkout properties.

It's recommended to use functions from calculations.py module to take in account plugin
manager.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional

from prices import TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import zero_money, zero_taxed_money
from ..discount import DiscountInfo
from ..order.interface import OrderTaxedPricesData
from .fetch import CheckoutLineInfo, ShippingMethodInfo
from .interface import CheckoutPricesData, CheckoutTaxedPricesData

if TYPE_CHECKING:
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo
    from ..order.models import OrderLine


def _calculate_base_line_unit_price(
    line_info: CheckoutLineInfo,
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> CheckoutPricesData:
    """Calculate base line unit price without voucher applied once per order."""
    variant = line_info.variant
    variant_price = variant.get_price(
        line_info.product,
        line_info.collections,
        channel,
        line_info.channel_listing,
        discounts or [],
        line_info.line.price_override,
    )

    if not discounts:
        undiscounted_variant_price = variant_price
    else:
        undiscounted_variant_price = variant.get_price(
            line_info.product,
            line_info.collections,
            channel,
            line_info.channel_listing,
            [],
            line_info.line.price_override,
        )

    if line_info.voucher and not line_info.voucher.apply_once_per_order:
        price_with_discounts = max(
            variant_price
            - line_info.voucher.get_discount_amount_for(variant_price, channel=channel),
            zero_money(variant_price.currency),
        )
    else:
        price_with_discounts = variant_price

    return CheckoutPricesData(
        undiscounted_price=quantize_price(
            undiscounted_variant_price, undiscounted_variant_price.currency
        ),
        price_with_sale=quantize_price(variant_price, variant_price.currency),
        price_with_discounts=quantize_price(
            price_with_discounts, price_with_discounts.currency
        ),
    )


def calculate_base_line_unit_price(
    line_info: CheckoutLineInfo,
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> CheckoutPricesData:
    """Calculate line unit prices including discounts and vouchers.

    Returns a three money values. Undiscounted price, price and price with voucher.
    Voucher is added to 'price_with_discounts' when line's product matches to products
    applicable for voucher.
    For voucher with 'apply once per order', the price will be included in unit price.
    'price' includes discount from sale if any valid exists.
    'price_with_discounts' includes voucher discount and sale discount if any valid
    exists.
    'undiscounted_price' is a price without any sale and voucher.
    """
    prices_data = calculate_base_line_total_price(
        line_info=line_info, channel=channel, discounts=discounts
    )
    quantity = line_info.line.quantity
    currency = prices_data.price_with_discounts.currency
    return CheckoutPricesData(
        undiscounted_price=quantize_price(
            prices_data.undiscounted_price / quantity, currency
        ),
        price_with_sale=quantize_price(
            prices_data.price_with_sale / quantity, currency
        ),
        price_with_discounts=quantize_price(
            prices_data.price_with_discounts / quantity, currency
        ),
    )


def calculate_base_line_total_price(
    line_info: CheckoutLineInfo,
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> CheckoutPricesData:
    """Calculate line total prices including discounts and vouchers.

    Returns a three money values. Undiscounted price, price and price with voucher.
    It calculates a unit prices and adds a voucher to line if voucher is applicable
    only once per order.
    'price' includes discount from sale if any valid exists.
    'price_with_discounts' includes voucher discount and sale discount if any valid
    exists.
    'undiscounted_price' is a price without any sale and voucher.
    """
    prices_data = _calculate_base_line_unit_price(
        line_info=line_info, channel=channel, discounts=discounts
    )
    if line_info.voucher and line_info.voucher.apply_once_per_order:
        variant_price_with_discounts = max(
            prices_data.price_with_sale
            - line_info.voucher.get_discount_amount_for(
                prices_data.price_with_sale, channel=channel
            ),
            zero_money(prices_data.price_with_sale.currency),
        )
        # we add -1 as we handle a case when voucher is applied only to single line
        # of the cheapest item
        quantity_without_voucher = line_info.line.quantity - 1
        prices_data = CheckoutPricesData(
            price_with_discounts=(
                prices_data.price_with_sale * quantity_without_voucher
                + variant_price_with_discounts
            ),
            price_with_sale=prices_data.price_with_sale * line_info.line.quantity,
            undiscounted_price=prices_data.undiscounted_price * line_info.line.quantity,
        )
    else:
        prices_data = CheckoutPricesData(
            price_with_sale=prices_data.price_with_sale * line_info.line.quantity,
            price_with_discounts=prices_data.price_with_discounts
            * line_info.line.quantity,
            undiscounted_price=prices_data.undiscounted_price * line_info.line.quantity,
        )
    prices_data.price_with_sale = quantize_price(
        prices_data.price_with_sale, prices_data.price_with_sale.currency
    )
    prices_data.undiscounted_price = quantize_price(
        prices_data.undiscounted_price, prices_data.undiscounted_price.currency
    )
    prices_data.price_with_discounts = quantize_price(
        prices_data.price_with_discounts, prices_data.price_with_discounts.currency
    )
    return prices_data


def base_checkout_delivery_price(
    checkout_info: "CheckoutInfo", lines=None
) -> TaxedMoney:
    """Calculate base (untaxed) price for any kind of delivery method."""
    delivery_method_info = checkout_info.delivery_method_info

    if isinstance(delivery_method_info, ShippingMethodInfo):
        return calculate_base_price_for_shipping_method(
            checkout_info, delivery_method_info, lines
        )

    return zero_taxed_money(checkout_info.checkout.currency)


def calculate_base_price_for_shipping_method(
    checkout_info: "CheckoutInfo",
    shipping_method_info: ShippingMethodInfo,
    lines=None,
) -> TaxedMoney:
    """Return checkout shipping price."""
    # FIXME: Optimize checkout.is_shipping_required
    shipping_method = shipping_method_info.delivery_method

    if lines is not None and all(isinstance(line, CheckoutLineInfo) for line in lines):
        from .utils import is_shipping_required

        shipping_required = is_shipping_required(lines)
    else:
        shipping_required = checkout_info.checkout.is_shipping_required()

    if not shipping_method or not shipping_required:
        return zero_taxed_money(checkout_info.checkout.currency)

    # Base price does not yet contain tax information,
    # which can be later applied by tax plugins
    return quantize_price(
        TaxedMoney(
            net=shipping_method.price,
            gross=shipping_method.price,
        ),
        checkout_info.checkout.currency,
    )


def base_checkout_total(
    checkout_info: "CheckoutInfo",
    discounts: Iterable[DiscountInfo],
    lines: Iterable["CheckoutLineInfo"],
) -> TaxedMoney:
    """Return the total cost of the checkout."""
    currency = checkout_info.checkout.currency
    line_totals = [
        base_checkout_line_total(
            line_info,
            checkout_info.channel,
            discounts,
        ).price_with_discounts
        for line_info in lines
    ]
    subtotal = sum(line_totals, zero_taxed_money(currency))

    shipping_price = base_checkout_delivery_price(checkout_info, lines)
    discount = checkout_info.checkout.discount

    zero = zero_taxed_money(currency)
    total = subtotal + shipping_price - discount
    # Discount is subtracted from both gross and net values, which may cause negative
    # net value if we are having a discount that covers whole price.
    # Comparing TaxedMoney objects works only on gross values. That is why we are
    # explicitly returning zero_taxed_money if total.gross is less or equal zero.
    if total.gross <= zero.gross:
        return zero
    return total


def base_checkout_lines_total(
    checkout_lines: Iterable["CheckoutLineInfo"],
    channel: "Channel",
    currency: str,
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> TaxedMoney:
    line_totals = [
        calculate_base_line_total_price(
            line,
            channel,
            discounts,
        ).price_with_sale
        for line in checkout_lines
    ]

    return sum(line_totals, zero_taxed_money(currency))


def base_checkout_line_total(
    checkout_line_info: "CheckoutLineInfo",
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> CheckoutTaxedPricesData:
    """Return the total price of this line."""
    prices_data = calculate_base_line_total_price(
        line_info=checkout_line_info, channel=channel, discounts=discounts
    )
    return CheckoutTaxedPricesData(
        price_with_sale=TaxedMoney(
            net=prices_data.price_with_sale, gross=prices_data.price_with_sale
        ),
        price_with_discounts=TaxedMoney(
            net=prices_data.price_with_discounts, gross=prices_data.price_with_discounts
        ),
        undiscounted_price=TaxedMoney(
            net=prices_data.undiscounted_price, gross=prices_data.undiscounted_price
        ),
    )


def base_order_line_total(order_line: "OrderLine") -> OrderTaxedPricesData:
    quantity = order_line.quantity
    price_with_discounts = (
        TaxedMoney(order_line.base_unit_price, order_line.base_unit_price) * quantity
    )
    undiscounted_price = (
        TaxedMoney(
            order_line.undiscounted_base_unit_price,
            order_line.undiscounted_base_unit_price,
        )
        * quantity
    )
    return OrderTaxedPricesData(
        undiscounted_price=undiscounted_price,
        price_with_discounts=price_with_discounts,
    )


def base_tax_rate(price: TaxedMoney):
    tax_rate = Decimal("0.0")
    # The condition will return False when unit_price.gross or unit_price.net is 0.0
    if not isinstance(price, Decimal) and all((price.gross, price.net)):
        tax_rate = price.tax / price.net
    return tax_rate


def base_checkout_line_unit_price(
    checkout_line_info: "CheckoutLineInfo",
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    prices_data = calculate_base_line_unit_price(
        line_info=checkout_line_info, channel=channel, discounts=discounts
    )
    return CheckoutTaxedPricesData(
        price_with_sale=TaxedMoney(
            net=prices_data.price_with_sale, gross=prices_data.price_with_sale
        ),
        price_with_discounts=TaxedMoney(
            net=prices_data.price_with_discounts, gross=prices_data.price_with_discounts
        ),
        undiscounted_price=TaxedMoney(
            net=prices_data.undiscounted_price, gross=prices_data.undiscounted_price
        ),
    )
