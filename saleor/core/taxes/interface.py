from typing import TYPE_CHECKING, List, Union

from django.conf import settings
from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from . import ZERO_TAXED_MONEY, TaxType
from .avatax import interface as avatax_interface
from .vatlayer import interface as vatlayer_interface

if TYPE_CHECKING:
    from ...discount.models import SaleQueryset
    from ...checkout.models import Checkout, CheckoutLine
    from ...product.models import Product
    from ...account.models import Address
    from ...order.models import OrderLine, Order


def calculate_checkout_total(
    checkout: "Checkout", discounts: "SaleQueryset"
) -> TaxedMoney:
    """Calculate total gross for checkout"""

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.calculate_checkout_total(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.calculate_checkout_total(checkout, discounts)

    total = checkout.get_total(discounts)
    return TaxedMoney(net=total, gross=total)


def calculate_checkout_subtotal(
    checkout: "Checkout", discounts: "SaleQueryset"
) -> TaxedMoney:
    """Calculate subtotal gross for checkout"""

    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.calculate_checkout_subtotal(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.calculate_checkout_subtotal(checkout, discounts)

    subtotal = checkout.get_subtotal(discounts)
    return TaxedMoney(net=subtotal, gross=subtotal)


def calculate_checkout_shipping(
    checkout: "Checkout", discounts: "SaleQueryset"
) -> TaxedMoney:
    """Calculate shipping gross for checkout"""
    if not checkout.shipping_method:
        return ZERO_TAXED_MONEY
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.calculate_checkout_shipping(checkout, discounts)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.calculate_checkout_shipping(checkout, discounts)
    total = checkout.shipping_method.get_total()
    return TaxedMoney(net=total, gross=total)


def calculate_order_shipping(order: "Order") -> TaxedMoney:
    """Calculate shipping price that assigned to order"""
    if settings.VATLAYER_ACCESS_KEY:
        return calculate_order_shipping(order)
    elif settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.calculate_order_shipping(order)
    price = order.shipping_method.price
    return TaxedMoney(net=price, gross=price)


def apply_taxes_to_shipping(price: Money, shipping_address: "Address") -> TaxedMoney:
    """Apply taxes for shipping methods that user can use during checkout"""
    if shipping_address:
        if settings.VATLAYER_ACCESS_KEY:
            return vatlayer_interface.apply_taxes_to_shipping(price, shipping_address)
        if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
            # For now we can't calculate product/shipping prices that are not directly
            # assigned to order. Avatax has api only to calculate prices based on
            # checkout/order data
            pass
    return TaxedMoney(net=price, gross=price)


def get_tax_rate_type_choices() -> List[TaxType]:
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.get_tax_rate_type_choices()
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.get_tax_rate_type_choices()
    return []


def calculate_checkout_line_total(
    checkout_line: "CheckoutLine", discounts: "SaleQueryset"
):
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.calculate_checkout_line_total(
            checkout_line, discounts
        )
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.calculate_checkout_line_total(checkout_line, discounts)
    total = checkout_line.get_total(discounts)
    return TaxedMoney(net=total, gross=total)


def calculate_order_line_unit(order_line: "OrderLine"):
    """It updates unit_price for a given order line based on current price of variant"""
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.calculate_order_line_unit(order_line)
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.calculate_order_line_unit(order_line)
    return order_line.unit_price


def apply_taxes_to_product(product: "Product", price: Money, country: Country):
    if settings.VATLAYER_ACCESS_KEY:
        return vatlayer_interface.apply_taxes_to_product(product, price, country)
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return TaxedMoney(net=price, gross=price)
    return TaxedMoney(net=price, gross=price)


def show_taxes_on_storefront() -> bool:
    """Specify if taxes are enabled"""
    if settings.VATLAYER_ACCESS_KEY:
        return True
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return False
    return False


def checkout_are_taxes_handled() -> bool:
    if settings.VATLAYER_ACCESS_KEY:
        return True
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return True
    return False


def apply_taxes_to_shipping_price_range(prices: MoneyRange, country: Country):
    if country:
        if settings.VATLAYER_ACCESS_KEY:
            return vatlayer_interface.apply_taxes_to_shipping_price_range(
                prices, country
            )
        if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
            pass
    start = TaxedMoney(net=prices.start, gross=prices.start)
    stop = TaxedMoney(net=prices.stop, gross=prices.stop)
    return TaxedMoneyRange(start=start, stop=stop)


def preprocess_order_creation(checkout: "Checkout"):
    if settings.AVATAX_USERNAME_OR_ACCOUNT and settings.AVATAX_PASSWORD_OR_LICENSE:
        return avatax_interface.preprocess_order_creation(checkout)


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
