from typing import TYPE_CHECKING, List, Union

from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ..taxes import TaxType, quantize_price
from .plugin import BasePlugin

if TYPE_CHECKING:
    from ...checkout.models import Checkout, CheckoutLine
    from ...product.models import Product
    from ...account.models import Address
    from ...order.models import OrderLine, Order


class DummyPlugin(BasePlugin):
    """Dummy plugin class which overwrites all base plugin methods. It should be used
    when any other plugins are disabled"""

    def calculate_checkout_total(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        total = checkout.get_total(discounts)
        return quantize_price(TaxedMoney(net=total, gross=total), total.currency)

    def calculate_checkout_subtotal(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        subtotal = checkout.get_subtotal(discounts)
        return quantize_price(
            TaxedMoney(net=subtotal, gross=subtotal), subtotal.currency
        )

    def calculate_checkout_shipping(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        total = checkout.get_shipping_price()
        total = TaxedMoney(net=total, gross=total)
        return quantize_price(total, total.currency)

    def calculate_order_shipping(self, order: "Order") -> TaxedMoney:
        shipping_price = order.shipping_method.price
        return quantize_price(
            TaxedMoney(net=shipping_price, gross=shipping_price),
            shipping_price.currency,
        )

    def apply_taxes_to_shipping(
        self, price: Money, shipping_address: "Address"
    ) -> TaxedMoney:
        return quantize_price(TaxedMoney(net=price, gross=price), price.currency)

    def get_tax_rate_type_choices(self) -> List[TaxType]:
        return []

    def calculate_checkout_line_total(
        self, checkout_line: "CheckoutLine", discounts: List["DiscountInfo"]
    ):
        total = checkout_line.get_total(discounts)
        return quantize_price(TaxedMoney(net=total, gross=total), total.currency)

    def calculate_order_line_unit(self, order_line: "OrderLine"):
        unit_price = order_line.unit_price
        return quantize_price(unit_price, unit_price.currency)

    def apply_taxes_to_product(
        self, product: "Product", price: Money, country: Country, **kwargs
    ):
        return quantize_price(TaxedMoney(net=price, gross=price), price.currency)

    def show_taxes_on_storefront(self) -> bool:
        return False

    def taxes_are_enabled(self) -> bool:
        return False

    def apply_taxes_to_shipping_price_range(self, prices: MoneyRange, country: Country):
        start = TaxedMoney(net=prices.start, gross=prices.start)
        stop = TaxedMoney(net=prices.stop, gross=prices.stop)
        return quantize_price(TaxedMoneyRange(start=start, stop=stop), start.currency)

    def preprocess_order_creation(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ):
        return

    def postprocess_order_creation(self, order: "Order"):
        return

    def assign_data_to_object_meta(
        self, obj: Union["Product", "ProductType"], tax_code: str
    ):
        return

    def get_data_from_object_meta(
        self, obj: Union["Product", "ProductType"]
    ) -> TaxType:
        return TaxType(code="", description="")
