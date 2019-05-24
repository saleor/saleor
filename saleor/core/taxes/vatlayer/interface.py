from collections import defaultdict
from decimal import Decimal

from django_prices_vatlayer.utils import get_tax_rate
from prices import TaxedMoney

from ....discount.models import SaleQueryset
from ....discount.utils import calculate_discounted_price
from . import get_taxed_shipping_price, get_taxes_for_address


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
