from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional, Union

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django_countries.fields import Country
from prices import Money, TaxedMoney

from ...core.taxes import TaxType
from ..base_plugin import BasePlugin, ConfigurationTypeField

if TYPE_CHECKING:
    # flake8: noqa
    from ...account.models import Address
    from ...checkout import CheckoutLineInfo
    from ...checkout.models import Checkout, CheckoutLine
    from ...discount import DiscountInfo
    from ...order.models import Order
    from ...product.models import Product, ProductType


class PluginSample(BasePlugin):
    PLUGIN_ID = "plugin.sample"
    PLUGIN_NAME = "PluginSample"
    PLUGIN_DESCRIPTION = "Test plugin description"
    DEFAULT_ACTIVE = True
    DEFAULT_CONFIGURATION = [
        {"name": "Username", "value": "admin"},
        {"name": "Password", "value": None},
        {"name": "Use sandbox", "value": False},
        {"name": "API private key", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "Username": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Username input field",
            "label": "Username",
        },
        "Password": {
            "type": ConfigurationTypeField.PASSWORD,
            "help_text": "Password input field",
            "label": "Password",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Use sandbox",
            "label": "Use sandbox",
        },
        "API private key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "API key",
            "label": "Private key",
        },
        "certificate": {
            "type": ConfigurationTypeField.SECRET_MULTILINE,
            "help_text": "",
            "label": "Multiline certificate",
        },
    }

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        if path == "/webhook/paid":
            return JsonResponse(data={"received": True, "paid": True})
        if path == "/webhook/failed":
            return JsonResponse(data={"received": True, "paid": False})
        return HttpResponseNotFound()

    def calculate_checkout_total(
        self, checkout, lines, address, discounts, previous_value
    ):
        total = Money("1.0", currency=checkout.currency)
        return TaxedMoney(total, total)

    def calculate_checkout_subtotal(
        self, checkout, lines, address, discounts, previous_value
    ):
        subtotal = Money("1.0", currency=checkout.currency)
        return TaxedMoney(subtotal, subtotal)

    def calculate_checkout_shipping(
        self, checkout, lines, address, discounts, previous_value
    ):
        price = Money("1.0", currency=checkout.currency)
        return TaxedMoney(price, price)

    def calculate_order_shipping(self, order, previous_value):
        price = Money("1.0", currency=order.currency)
        return TaxedMoney(price, price)

    def calculate_checkout_line_total(
        self,
        checkout,
        checkout_line,
        variant,
        product,
        collections,
        address,
        channel,
        channel_listing,
        discounts,
        previous_value,
    ):
        price = Money("1.0", currency=checkout_line.checkout.currency)
        return TaxedMoney(price, price)

    def calculate_checkout_line_unit_price(
        self, total_line_price: TaxedMoney, quantity: int, previous_value: TaxedMoney
    ):
        return total_line_price / quantity

    def calculate_order_line_unit(self, order_line, previous_value):
        currency = order_line.unit_price.currency
        price = Money("1.0", currency)
        return TaxedMoney(price, price)

    def get_tax_rate_type_choices(self, previous_value):
        return [TaxType(code="123", description="abc")]

    def show_taxes_on_storefront(self, previous_value: bool) -> bool:
        return True

    def apply_taxes_to_product(self, product, price, country, previous_value, **kwargs):
        price = Money("1.0", price.currency)
        return TaxedMoney(price, price)

    def apply_taxes_to_shipping(
        self, price, shipping_address, previous_value
    ) -> TaxedMoney:
        price = Money("1.0", price.currency)
        return TaxedMoney(price, price)

    def get_tax_rate_percentage_value(
        self, obj: Union["Product", "ProductType"], country: Country, previous_value
    ) -> Decimal:
        return Decimal("15.0").quantize(Decimal("1."))

    def get_checkout_line_tax_rate(
        self,
        checkout: "Checkout",
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: Decimal,
    ) -> Decimal:
        return Decimal("0.080").quantize(Decimal(".01"))

    def get_order_line_tax_rate(
        self,
        order: "Order",
        product: "Product",
        address: Optional["Address"],
        previous_value: Decimal,
    ) -> Decimal:
        return Decimal("0.080").quantize(Decimal(".01"))

    def get_checkout_shipping_tax_rate(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: Decimal,
    ):
        return Decimal("0.080").quantize(Decimal(".01"))

    def get_order_shipping_tax_rate(self, order: "Order", previous_value: Decimal):
        return Decimal("0.080").quantize(Decimal(".01"))


class PluginInactive(BasePlugin):
    PLUGIN_ID = "plugin.inactive"
    PLUGIN_NAME = "PluginInactive"
    PLUGIN_DESCRIPTION = "Test plugin description_2"


class ActivePlugin(BasePlugin):
    PLUGIN_ID = "plugin.active"
    PLUGIN_NAME = "Active"
    PLUGIN_DESCRIPTION = "Not working"
    DEFAULT_ACTIVE = True


class ActivePaymentGateway(BasePlugin):
    PLUGIN_ID = "gateway.active"
    CLIENT_CONFIG = [
        {"field": "foo", "value": "bar"},
    ]
    PLUGIN_NAME = "braintree"
    DEFAULT_ACTIVE = True
    SUPPORTED_CURRENCIES = ["USD"]

    def process_payment(self, payment_information, previous_value):
        pass

    def get_supported_currencies(self, previous_value):
        return self.SUPPORTED_CURRENCIES

    def get_payment_config(self, previous_value):
        return self.CLIENT_CONFIG


class ActiveDummyPaymentGateway(BasePlugin):
    PLUGIN_ID = "sampleDummy.active"
    CLIENT_CONFIG = [
        {"field": "foo", "value": "bar"},
    ]
    PLUGIN_NAME = "SampleDummy"
    DEFAULT_ACTIVE = True
    SUPPORTED_CURRENCIES = ["EUR", "USD"]

    def process_payment(self, payment_information, previous_value):
        pass

    def get_supported_currencies(self, previous_value):
        return self.SUPPORTED_CURRENCIES

    def get_payment_config(self, previous_value):
        return self.CLIENT_CONFIG


class InactivePaymentGateway(BasePlugin):
    PLUGIN_ID = "gateway.inactive"
    PLUGIN_NAME = "stripe"

    def process_payment(self, payment_information, previous_value):
        pass
