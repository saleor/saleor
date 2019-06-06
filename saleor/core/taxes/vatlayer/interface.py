from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING

from django_countries.fields import Country
from django_prices_vatlayer.utils import get_tax_rate, get_tax_rate_types
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ....core import TaxRateType  # FIXME this should be placed in VatLayer module
from .. import ZERO_TAXED_MONEY
from . import (
    DEFAULT_TAX_RATE_NAME,
    apply_tax_to_price,
    get_taxed_shipping_price,
    get_taxes_for_address,
    get_taxes_for_country,
)

if TYPE_CHECKING:
    from ....discount.models import SaleQueryset
    from ....checkout.models import Checkout, CheckoutLine
    from ....product.models import Product, ProductVariant
    from ....account.models import Address


def get_total_gross(checkout: "Checkout", discounts: "SaleQueryset") -> TaxedMoney:
    """Calculate total gross for checkout by using vatlayer"""
    return (
        get_subtotal_gross(checkout, discounts)
        + get_shipping_gross(checkout, discounts)
        - checkout.discount_amount
    )


def get_subtotal_gross(checkout: "Checkout", discounts: "SaleQueryset") -> TaxedMoney:
    """Calculate subtotal gross for checkout"""
    address = checkout.shipping_address or checkout.billing_address
    lines = checkout.lines.prefetch_related("variant__product__product_type")
    lines_total = ZERO_TAXED_MONEY
    for line in lines:
        price = line.variant.get_price(discounts)
        lines_total += line.quantity * apply_taxes_to_variant(
            line.variant, price, address.country
        )
    return lines_total


def get_shipping_gross(checkout: "Checkout", _: "SaleQueryset") -> TaxedMoney:
    """Calculate shipping gross for checkout"""
    address = checkout.shipping_address or checkout.billing_address
    taxes = get_taxes_for_address(address)
    return get_taxed_shipping_price(checkout.shipping_method.price, taxes)


def get_lines_with_unit_tax(checkout: "Checkout", discounts: "SaleQueryset"):
    lines_taxes = defaultdict(lambda: Decimal("0.0"))

    address = checkout.shipping_address or checkout.billing_address
    taxes = get_taxes_for_address(address)
    lines = checkout.lines.prefetch_related("variant__product__product_type")
    for line in lines:
        price = line.variant.get_price(discounts)

        # FIXME tax_rate belongs to vatlayer. We should transfer it to metadata somehow
        tax_rate_name = (
            line.variant.product.tax_rate or line.variant.product.product_type.tax_rate
        )
        tax_rate = get_tax_rate(taxes, tax_rate_name)
        if not tax_rate:
            continue
        tax_rate = Decimal(tax_rate / 100)
        lines_taxes[line.variant.sku] = price.amount * tax_rate

    return [(line, lines_taxes[line.variant.sku]) for line in checkout.lines.all()]


def get_line_total_gross(checkout_line: "CheckoutLine", discounts: "SaleQueryset"):
    address = (
        checkout_line.checkout.shipping_address
        or checkout_line.checkout.billing_address
    )
    price = checkout_line.variant.get_price(discounts) * checkout_line.quantity
    return apply_taxes_to_variant(checkout_line.variant, price, address.country)


def apply_taxes_to_shipping(price: Money, shipping_address: "Address"):
    taxes = get_taxes_for_country(shipping_address.country)
    return get_taxed_shipping_price(price, taxes)


def get_tax_rate_type_choices():
    rate_types = get_tax_rate_types() + [DEFAULT_TAX_RATE_NAME]
    translations = dict(TaxRateType.CHOICES)
    choices = [
        (rate_name, translations.get(rate_name, "---------"))
        for rate_name in rate_types
    ]
    # sort choices alphabetically by translations
    return sorted(choices, key=lambda x: x[1])


def apply_taxes_to_variant(
    variant: "ProductVariant", price: "Money", country: "Country"
) -> TaxedMoney:
    taxes = None
    if variant.product.charge_taxes and country:
        taxes = get_taxes_for_country(country)
    tax_rate = variant.product.tax_rate or variant.product.product_type.tax_rate
    return apply_tax_to_price(taxes, tax_rate, price)


def apply_taxes_to_product(
    product: "Product", price: Money, country: Country
) -> TaxedMoney:
    taxes = None
    if product.charge_taxes and country:
        taxes = get_taxes_for_country(country)
    tax_rate = product.tax_rate or product.product_type.tax_rate
    return apply_tax_to_price(taxes, tax_rate, price)


def apply_taxes_to_shipping_price_range(
    prices: MoneyRange, country: "Country"
) -> TaxedMoneyRange:
    taxes = None
    if country:
        taxes = get_taxes_for_country(country)
    return get_taxed_shipping_price(prices, taxes)
