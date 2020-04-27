from decimal import Decimal
from typing import TYPE_CHECKING, Union

from django_countries.fields import Country
from prices import Money, TaxedMoney

from saleor.core.taxes import TaxType
from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from saleor.plugins.models import PluginConfiguration
from saleor.product.models import Product, ProductType

if TYPE_CHECKING:
    # flake8: noqa
    from saleor.product.models import Product, ProductType
    from django.db.models import QuerySet


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
    }

    def calculate_checkout_total(self, checkout, lines, discounts, previous_value):
        total = Money("1.0", currency=checkout.currency)
        return TaxedMoney(total, total)

    def calculate_checkout_subtotal(self, checkout, lines, discounts, previous_value):
        subtotal = Money("1.0", currency=checkout.currency)
        return TaxedMoney(subtotal, subtotal)

    def calculate_checkout_shipping(self, checkout, lines, discounts, previous_value):
        price = Money("1.0", currency=checkout.currency)
        return TaxedMoney(price, price)

    def calculate_order_shipping(self, order, previous_value):
        price = Money("1.0", currency=order.currency)
        return TaxedMoney(price, price)

    def calculate_checkout_line_total(self, checkout_line, discounts, previous_value):
        price = Money("1.0", currency=checkout_line.checkout.currency)
        return TaxedMoney(price, price)

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
    CLIENT_CONFIG = [{"field": "foo", "value": "bar"}]
    PLUGIN_NAME = "braintree"
    DEFAULT_ACTIVE = True

    def process_payment(self, payment_information, previous_value):
        pass

    def get_payment_config(self, previous_value):
        return self.CLIENT_CONFIG


class InactivePaymentGateway(BasePlugin):
    PLUGIN_ID = "gateway.inactive"
    PLUGIN_NAME = "stripe"

    def process_payment(self, payment_information, previous_value):
        pass
