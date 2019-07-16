from typing import TYPE_CHECKING, List, Union

from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

if TYPE_CHECKING:
    from ..taxes import TaxType
    from ...checkout.models import Checkout, CheckoutLine
    from ...product.models import Product
    from ...account.models import Address
    from ...order.models import OrderLine, Order


class BasePlugin:
    """Abstract class for storing all methods available for any plugin."""

    def calculate_checkout_total(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        raise NotImplementedError()

    def calculate_checkout_subtotal(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        raise NotImplementedError()

    def calculate_checkout_shipping(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        raise NotImplementedError()

    def calculate_order_shipping(self, order: "Order") -> TaxedMoney:
        raise NotImplementedError()

    def calculate_checkout_line_total(
        self, checkout_line: "CheckoutLine", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        raise NotImplementedError()

    def calculate_order_line_unit(self, order_line: "OrderLine") -> TaxedMoney:
        raise NotImplementedError()

    def get_tax_rate_type_choices(self) -> List["TaxType"]:
        raise NotImplementedError()

    def show_taxes_on_storefront(self) -> bool:
        raise NotImplementedError()

    def taxes_are_enabled(self) -> bool:
        raise NotImplementedError()

    def apply_taxes_to_shipping_price_range(
        self, prices: MoneyRange, country: Country
    ) -> TaxedMoneyRange:
        raise NotImplementedError()

    def apply_taxes_to_shipping(
        self, price: Money, shipping_address: "Address"
    ) -> TaxedMoney:
        raise NotImplementedError()

    def apply_taxes_to_product(
        self, product: "Product", price: Money, country: Country, **kwargs
    ):
        raise NotImplementedError()

    def preprocess_order_creation(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ):
        raise NotImplementedError()

    def postprocess_order_creation(self, order: "Order"):
        raise NotImplementedError()

    def assign_data_to_object_meta(
        self, obj: Union["Product", "ProductType"], data: str
    ):
        raise NotImplementedError()

    def get_data_from_object_meta(
        self, obj: Union["Product", "ProductType"]
    ) -> "TaxType":
        raise NotImplementedError()
