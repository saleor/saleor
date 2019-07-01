from typing import TYPE_CHECKING, List, Union

from django.conf import settings
from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from . import TaxType, quantize_price
from .avatax import interface as avatax_interface
from .vatlayer import interface as vatlayer_interface

if TYPE_CHECKING:
    from ...checkout.models import Checkout, CheckoutLine
    from ...product.models import Product
    from ...account.models import Address
    from ...order.models import OrderLine, Order


def calculate_checkout_total(
    checkout: "Checkout", discounts: List["DiscountInfo"]
) -> TaxedMoney:
    """Calculate total gross for checkout"""

    total = None
    if settings.VATLAYER_ACCESS_KEY:
        total = vatlayer_interface.calculate_checkout_total(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        total = avatax_interface.calculate_checkout_total(checkout, discounts)

    if total:
        return quantize_price(total, total.currency)

    total = checkout.get_total(discounts)
    return quantize_price(TaxedMoney(net=total, gross=total), total.currency)


def calculate_checkout_subtotal(
    checkout: "Checkout", discounts: List["DiscountInfo"]
) -> TaxedMoney:
    """Calculate subtotal gross for checkout"""

    subtotal = None
    if settings.VATLAYER_ACCESS_KEY:
        subtotal = vatlayer_interface.calculate_checkout_subtotal(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        subtotal = avatax_interface.calculate_checkout_subtotal(checkout, discounts)

    if subtotal:
        return quantize_price(subtotal, subtotal.currency)

    subtotal = checkout.get_subtotal(discounts)
    return quantize_price(TaxedMoney(net=subtotal, gross=subtotal), subtotal.currency)


def calculate_checkout_shipping(
    checkout: "Checkout", discounts: List["DiscountInfo"]
) -> TaxedMoney:
    """Calculate shipping gross for checkout"""
    total = checkout.get_shipping_price()
    total = TaxedMoney(net=total, gross=total)
    if not checkout.shipping_method:
        return quantize_price(total, total.currency)
    if settings.VATLAYER_ACCESS_KEY:
        total = vatlayer_interface.calculate_checkout_shipping(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        total = avatax_interface.calculate_checkout_shipping(checkout, discounts)
    return quantize_price(total, total.currency)


def calculate_order_shipping(order: "Order") -> TaxedMoney:
    """Calculate shipping price that assigned to order"""
    shipping_price = None
    if settings.VATLAYER_ACCESS_KEY:
        shipping_price = vatlayer_interface.calculate_order_shipping(order)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        shipping_price = avatax_interface.calculate_order_shipping(order)

    if shipping_price:
        return quantize_price(shipping_price, shipping_price.currency)
    shipping_price = order.shipping_method.price
    return quantize_price(
        TaxedMoney(net=shipping_price, gross=shipping_price), shipping_price.currency
    )


def apply_taxes_to_shipping(price: Money, shipping_address: "Address") -> TaxedMoney:
    """Apply taxes for shipping methods that user can use during checkout"""
    if shipping_address:
        if settings.VATLAYER_ACCESS_KEY:
            return quantize_price(
                vatlayer_interface.apply_taxes_to_shipping(price, shipping_address),
                price.currency,
            )
        if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
            # For now we can't calculate product/shipping prices that are not directly
            # assigned to order. Avatax has api only to calculate prices based on
            # checkout/order data
            pass
    return quantize_price(TaxedMoney(net=price, gross=price), price.currency)


def get_tax_rate_type_choices() -> List[TaxType]:
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_tax_rate_type_choices()
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_tax_rate_type_choices()
    return []


def calculate_checkout_line_total(
    checkout_line: "CheckoutLine", discounts: List["DiscountInfo"]
):
    total = None
    if settings.VATLAYER_ACCESS_KEY:
        total = vatlayer_interface.calculate_checkout_line_total(
            checkout_line, discounts
        )
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        total = avatax_interface.calculate_checkout_line_total(checkout_line, discounts)
    if total:
        return quantize_price(total, total.currency)
    total = checkout_line.get_total(discounts)
    return quantize_price(TaxedMoney(net=total, gross=total), total.currency)


def calculate_order_line_unit(order_line: "OrderLine"):
    """It updates unit_price for a given order line based on current price of variant"""
    if settings.VATLAYER_ACCESS_KEY:
        unit_price = vatlayer_interface.calculate_order_line_unit(order_line)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        unit_price = avatax_interface.calculate_order_line_unit(order_line)
    else:
        unit_price = order_line.unit_price

    return quantize_price(unit_price, unit_price.currency)


def apply_taxes_to_product(
    product: "Product", price: Money, country: Country, **kwargs
):
    if settings.VATLAYER_ACCESS_KEY:
        return quantize_price(
            vatlayer_interface.apply_taxes_to_product(
                product, price, country, **kwargs
            ),
            price.currency,
        )
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        pass
    return quantize_price(TaxedMoney(net=price, gross=price), price.currency)


def show_taxes_on_storefront() -> bool:
    """Specify if taxes are enabled"""
    if settings.VATLAYER_ACCESS_KEY:
        return True
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return False
    return False


def taxes_are_enabled() -> bool:
    if settings.VATLAYER_ACCESS_KEY:
        return True
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return True
    return False


def apply_taxes_to_shipping_price_range(prices: MoneyRange, country: Country):
    if country:
        if settings.VATLAYER_ACCESS_KEY:
            return quantize_price(
                vatlayer_interface.apply_taxes_to_shipping_price_range(prices, country),
                prices.currency,
            )
        if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
            pass
    start = TaxedMoney(net=prices.start, gross=prices.start)
    stop = TaxedMoney(net=prices.stop, gross=prices.stop)
    return quantize_price(TaxedMoneyRange(start=start, stop=stop), start.currency)


def preprocess_order_creation(checkout: "Checkout", discounts: List["DiscountInfo"]):
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.preprocess_order_creation(checkout, discounts)


# FIXME this should be converted to the plugin action after we introduce plugin
# architecture
def postprocess_order_creation(order: "Order"):
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.postprocess_order_creation(order)


def assign_tax_to_object_meta(obj: Union["Product", "ProductType"], tax_code: str):
    if settings.VATLAYER_ACCESS_KEY:
        vatlayer_interface.assign_tax_to_object_meta(obj, tax_code)
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        avatax_interface.assign_tax_to_object_meta(obj, tax_code)


def get_tax_from_object_meta(obj: Union["Product", "ProductType"],) -> TaxType:
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_tax_from_object_meta(obj)
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_tax_from_object_meta(obj)
    return TaxType(code="", description="")
