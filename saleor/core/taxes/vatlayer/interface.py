from collections import defaultdict
from decimal import Decimal

from django_countries.fields import Country
from django_prices_vatlayer.utils import get_tax_rate, get_tax_rate_types
from prices import TaxedMoney

from ....core import TaxRateType  # FIXME this should be placed in VatLayer module
from ....discount.models import SaleQueryset
from ....discount.utils import calculate_discounted_price
from . import (
    DEFAULT_TAX_RATE_NAME,
    apply_tax_to_price,
    get_taxed_shipping_price,
    get_taxes_for_address,
    get_taxes_for_country,
)


def get_total_gross(checkout: "Checkout", discounts: SaleQueryset) -> TaxedMoney:
    """Calculate total gross for checkout by using vatlayer"""
    address = checkout.shipping_address or checkout.billing_address
    taxes = get_taxes_for_address(address)
    return checkout.get_total(discounts, taxes)


def get_subtotal_gross(checkout: "Checkout", discounts: SaleQueryset) -> TaxedMoney:
    """Calculate subtotal gross for checkout"""
    address = checkout.shipping_address or checkout.billing_address
    taxes = get_taxes_for_address(address)
    return checkout.get_total(discounts, taxes)


def get_shipping_gross(checkout: "Checkout", discounts: SaleQueryset) -> TaxedMoney:
    """Calculate shipping gross for checkout"""
    address = checkout.shipping_address or checkout.billing_address
    taxes = get_taxes_for_address(address)
    return get_taxed_shipping_price(checkout.shipping_method.price, taxes)


def get_lines_with_taxes(checkout: "Checkout", discounts):
    lines_taxes = defaultdict(lambda: Decimal("0.0"))

    address = checkout.shipping_address or checkout.billing_address
    taxes = get_taxes_for_address(address)
    for line in checkout.lines.all():
        price = calculate_discounted_price(
            line.variant.product, line.variant.base_price, discounts
        )
        tax_rate_name = (
            line.variant.product.tax_rate or line.variant.product.product_type.tax_rate
        )
        tax_rate = get_tax_rate(taxes, tax_rate_name)
        if not tax_rate:
            continue
        tax_rate = Decimal(tax_rate / 100)
        lines_taxes[line.variant.sku] = price.amount * tax_rate

    return [(line, lines_taxes[line.variant.sku]) for line in checkout.lines.all()]


def apply_taxes_to_shipping(price: "Money", shipping_address: "Address"):
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


def apply_taxes_to_variant(variant: "ProductVariant", price, country: "Country"):
    taxes = get_taxes_for_country(country)
    tax_rate = variant.product.tax_rate or variant.product.product_type.tax_rate
    return apply_tax_to_price(taxes, tax_rate, price)


def apply_taxes_to_product(product: "Product", price: "Money", country: "Country"):
    taxes = None
    if country:
        taxes = get_taxes_for_country(country)
    tax_rate = product.tax_rate or product.product_type.tax_rate
    return apply_tax_to_price(taxes, tax_rate, price)
