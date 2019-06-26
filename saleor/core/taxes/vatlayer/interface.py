from typing import TYPE_CHECKING, List, Union

from django_countries.fields import Country
from django_prices_vatlayer.utils import get_tax_rate_types
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from .. import ZERO_TAXED_MONEY, TaxType
from . import (
    DEFAULT_TAX_RATE_NAME,
    TaxRateType,
    apply_tax_to_price,
    get_taxed_shipping_price,
    get_taxes_for_address,
    get_taxes_for_country,
)

if TYPE_CHECKING:
    from ....checkout.models import Checkout, CheckoutLine
    from ....product.models import Product
    from ....account.models import Address
    from ....order.models import Order, OrderLine


META_FIELD = "vatlayer"


def calculate_checkout_total(
    checkout: "Checkout", discounts: List["DiscountInfo"]
) -> TaxedMoney:
    """Calculate total gross for checkout by using vatlayer"""
    return (
        calculate_checkout_subtotal(checkout, discounts)
        + calculate_checkout_shipping(checkout, discounts)
        - checkout.discount_amount
    )


def calculate_checkout_subtotal(
    checkout: "Checkout", discounts: List["DiscountInfo"]
) -> TaxedMoney:
    """Calculate subtotal gross for checkout"""
    address = checkout.shipping_address or checkout.billing_address
    lines = checkout.lines.prefetch_related("variant__product__product_type")
    lines_total = ZERO_TAXED_MONEY
    for line in lines:
        price = line.variant.get_price(discounts)
        lines_total += line.quantity * apply_taxes_to_product(
            line.variant.product, price, address.country if address else None
        )
    return lines_total


def calculate_checkout_shipping(
    checkout: "Checkout", _: List["DiscountInfo"]
) -> TaxedMoney:
    """Calculate shipping gross for checkout"""
    address = checkout.shipping_address or checkout.billing_address
    taxes = get_taxes_for_address(address)
    if not checkout.shipping_method:
        return ZERO_TAXED_MONEY
    return get_taxed_shipping_price(checkout.shipping_method.price, taxes)


def calculate_order_shipping(order: "Order") -> TaxedMoney:
    address = order.shipping_address or order.billing_address
    taxes = get_taxes_for_address(address)
    if not order.shipping_method:
        return ZERO_TAXED_MONEY
    return get_taxed_shipping_price(order.shipping_method.price, taxes)


def calculate_order_line_unit(order_line: "OrderLine") -> TaxedMoney:
    address = order_line.order.shipping_address or order_line.order.billing_address
    country = address.country if address else None
    variant = order_line.variant
    return apply_taxes_to_product(variant.product, order_line.unit_price_net, country)


def calculate_checkout_line_total(
    checkout_line: "CheckoutLine", discounts: List["DiscountInfo"]
):
    address = (
        checkout_line.checkout.shipping_address
        or checkout_line.checkout.billing_address
    )
    price = checkout_line.variant.get_price(discounts) * checkout_line.quantity
    country = address.country if address else None
    return apply_taxes_to_product(checkout_line.variant.product, price, country)


def apply_taxes_to_shipping(price: Money, shipping_address: "Address"):
    taxes = get_taxes_for_country(shipping_address.country)
    return get_taxed_shipping_price(price, taxes)


def get_tax_rate_type_choices() -> List[TaxType]:
    rate_types = get_tax_rate_types() + [DEFAULT_TAX_RATE_NAME]
    choices = [
        TaxType(code=rate_name, description=rate_name) for rate_name in rate_types
    ]
    # sort choices alphabetically by translations
    return sorted(choices, key=lambda x: x.code)


def apply_taxes_to_product(
    product: "Product", price: Money, country: Country, **kwargs
) -> TaxedMoney:
    taxes = kwargs.get("taxes")
    if country and not taxes:
        # FIXME After we introduce plugin architecture, taxes will be cached on the
        #  plugin level and there will be no need to pass it from view functions.
        #  This is only temporary approach to limit redis and db hits
        taxes = get_taxes_for_country(country)
    if not product.charge_taxes:
        taxes = None
    product_tax_rate = get_tax_from_object_meta(product).code
    tax_rate = product_tax_rate or get_tax_from_object_meta(product.product_type).code
    return apply_tax_to_price(taxes, tax_rate, price)


def apply_taxes_to_shipping_price_range(
    prices: MoneyRange, country: "Country"
) -> TaxedMoneyRange:
    taxes = None
    if country:
        taxes = get_taxes_for_country(country)
    return get_taxed_shipping_price(prices, taxes)


def assign_tax_to_object_meta(obj: Union["Product", "ProductType"], tax_code: str):
    if tax_code not in dict(TaxRateType.CHOICES):
        return
    if not hasattr(obj, "meta"):
        return
    if "taxes" not in obj.meta:
        obj.meta["taxes"] = {}
    obj.meta["taxes"][META_FIELD] = {"code": tax_code, "description": tax_code}


def get_tax_from_object_meta(obj: Union["Product", "ProductType"]) -> TaxType:
    if not hasattr(obj, "meta"):
        return TaxType(code="", description="")
    tax = obj.meta.get("taxes", {}).get(META_FIELD, {})

    return TaxType(code=tax.get("code", ""), description=tax.get("description", ""))
