from typing import TYPE_CHECKING, Any, List, Union

from django.conf import settings
from django_countries.fields import Country
from django_prices_vatlayer.utils import get_tax_rate_types
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ....taxes import TaxType
from ...plugin import BasePlugin
from . import (
    DEFAULT_TAX_RATE_NAME,
    TaxRateType,
    apply_tax_to_price,
    get_taxed_shipping_price,
    get_taxes_for_address,
    get_taxes_for_country,
)

if TYPE_CHECKING:

    from .....checkout.models import Checkout, CheckoutLine
    from .....product.models import Product
    from .....account.models import Address
    from .....order.models import OrderLine, Order


class VatlayerPlugin(BasePlugin):
    META_FIELD = "vatlayer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enabled = bool(settings.VATLAYER_ACCESS_KEY)

    def _skip_plugin(self, previous_value: Union[TaxedMoney, TaxedMoneyRange]) -> bool:
        if not self._enabled:
            return True

        # The previous plugin already calculated taxes so we can skip our logic
        if isinstance(previous_value, TaxedMoneyRange):
            start = previous_value.start
            stop = previous_value.stop

            return start.net != start.gross and stop.net != stop.gross

        if isinstance(previous_value, TaxedMoney):
            return previous_value.net != previous_value.gross
        return False

    def calculate_checkout_total(
        self,
        checkout: "Checkout",
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:

        if self._skip_plugin(previous_value):
            return previous_value

        zero_total = Money(0, currency=previous_value.currency)
        taxed_zero = TaxedMoney(zero_total, zero_total)

        return (
            self.calculate_checkout_subtotal(checkout, discounts, previous_value)
            + self.calculate_checkout_shipping(checkout, discounts, taxed_zero)
            - checkout.discount_amount
        )

    def calculate_checkout_subtotal(
        self,
        checkout: "Checkout",
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        """Calculate subtotal gross for checkout"""
        if self._skip_plugin(previous_value):
            return previous_value

        address = checkout.shipping_address or checkout.billing_address
        lines = checkout.lines.prefetch_related("variant__product__product_type")
        zero_total = Money(0, currency=previous_value.currency)

        lines_total = TaxedMoney(net=zero_total, gross=zero_total)
        for line in lines:
            price = line.variant.get_price(discounts)
            lines_total += line.quantity * self.apply_taxes_to_product(
                line.variant.product, price, address.country if address else None, price
            )
        return lines_total

    def calculate_checkout_shipping(
        self,
        checkout: "Checkout",
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        """Calculate shipping gross for checkout"""
        if self._skip_plugin(previous_value):
            return previous_value

        address = checkout.shipping_address or checkout.billing_address
        taxes = get_taxes_for_address(address)
        if not checkout.shipping_method:
            return previous_value

        return get_taxed_shipping_price(checkout.shipping_method.price, taxes)

    def calculate_order_shipping(
        self, order: "Order", previous_value: TaxedMoney
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        address = order.shipping_address or order.billing_address
        taxes = get_taxes_for_address(address)
        if not order.shipping_method:
            return previous_value
        return get_taxed_shipping_price(order.shipping_method.price, taxes)

    def calculate_checkout_line_total(
        self,
        checkout_line: "CheckoutLine",
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        address = (
            checkout_line.checkout.shipping_address
            or checkout_line.checkout.billing_address
        )
        price = checkout_line.variant.get_price(discounts) * checkout_line.quantity
        country = address.country if address else None
        return self.apply_taxes_to_product(
            checkout_line.variant.product, price, country, previous_value
        )

    def calculate_order_line_unit(
        self, order_line: "OrderLine", previous_value: TaxedMoney
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        address = order_line.order.shipping_address or order_line.order.billing_address
        country = address.country if address else None
        variant = order_line.variant
        return self.apply_taxes_to_product(
            variant.product, order_line.unit_price_net, country, previous_value
        )

    def get_tax_rate_type_choices(
        self, previous_value: List["TaxType"]
    ) -> List["TaxType"]:
        if not self._enabled:
            return previous_value

        rate_types = get_tax_rate_types() + [DEFAULT_TAX_RATE_NAME]
        choices = [
            TaxType(code=rate_name, description=rate_name) for rate_name in rate_types
        ]
        # sort choices alphabetically by translations
        return sorted(choices, key=lambda x: x.code)

    def show_taxes_on_storefront(self, previous_value: bool) -> bool:
        if not self._enabled:
            return previous_value
        return True

    def taxes_are_enabled(self, previous_value: bool) -> bool:
        if not self._enabled:
            return previous_value
        return True

    def apply_taxes_to_shipping_price_range(
        self, prices: MoneyRange, country: Country, previous_value: TaxedMoneyRange
    ) -> TaxedMoneyRange:
        if self._skip_plugin(previous_value):
            return previous_value

        taxes = None
        if country:
            taxes = get_taxes_for_country(country)
        return get_taxed_shipping_price(prices, taxes)

    def apply_taxes_to_shipping(
        self, price: Money, shipping_address: "Address", previous_value: TaxedMoney
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        taxes = get_taxes_for_country(shipping_address.country)
        return get_taxed_shipping_price(price, taxes)

    def apply_taxes_to_product(
        self,
        product: "Product",
        price: Money,
        country: Country,
        previous_value: TaxedMoney,
        **kwargs,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        taxes = kwargs.get("taxes")
        if country and not taxes:
            # FIXME After we introduce plugin architecture, taxes will be cached on the
            #  plugin level and there will be no need to pass it from view functions.
            #  This is only temporary approach to limit redis and db hits
            taxes = get_taxes_for_country(country)
        if not product.charge_taxes:
            taxes = None
        product_tax_rate = self.__get_tax_code_from_object_meta(product).code
        tax_rate = (
            product_tax_rate
            or self.__get_tax_code_from_object_meta(product.product_type).code
        )
        return apply_tax_to_price(taxes, tax_rate, price)

    def assign_tax_code_to_object_meta(
        self, obj: Union["Product", "ProductType"], tax_code: str, previous_value: Any
    ):
        if not self._enabled:
            return previous_value

        if tax_code not in dict(TaxRateType.CHOICES):
            return previous_value
        if not hasattr(obj, "meta"):
            return previous_value
        if "taxes" not in obj.meta:
            obj.meta["taxes"] = {}
        obj.meta["taxes"][self.META_FIELD] = {"code": tax_code, "description": tax_code}
        return previous_value

    def get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType"], previous_value: "TaxType"
    ) -> "TaxType":
        if not self._enabled:
            return previous_value
        return self.__get_tax_code_from_object_meta(obj)

    def __get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType"]
    ) -> "TaxType":
        tax = obj.meta.get("taxes", {}).get(self.META_FIELD, {})
        return TaxType(code=tax.get("code", ""), description=tax.get("description", ""))
