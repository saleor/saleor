from decimal import Decimal
from typing import Union

from django_countries.fields import Country
from prices import Money, TaxedMoney

from saleor.core.taxes import TaxType
from saleor.extensions import ConfigurationTypeField
from saleor.extensions.base_plugin import BasePlugin
from saleor.extensions.models import PluginConfiguration


class PluginSample(BasePlugin):
    PLUGIN_NAME = "PluginSample"
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

    @classmethod
    def _get_default_configuration(cls):
        return {
            "name": "PluginSample",
            "description": "Test plugin description",
            "active": True,
            "configuration": [
                {"name": "Username", "value": "admin"},
                {"name": "Password", "value": None},
                {"name": "Use sandbox", "value": False},
                {"name": "API private key", "value": None},
            ],
        }

    def calculate_checkout_total(self, checkout, discounts, previous_value):
        total = Money("1.0", currency=checkout.get_total().currency)
        return TaxedMoney(total, total)

    def calculate_checkout_subtotal(self, checkout, discounts, previous_value):
        subtotal = Money("1.0", currency=checkout.get_total().currency)
        return TaxedMoney(subtotal, subtotal)

    def calculate_checkout_shipping(self, checkout, discounts, previous_value):
        price = Money("1.0", currency=checkout.get_total().currency)
        return TaxedMoney(price, price)

    def calculate_order_shipping(self, order, previous_value):
        price = Money("1.0", currency=order.total.currency)
        return TaxedMoney(price, price)

    def calculate_checkout_line_total(self, checkout_line, discounts, previous_value):
        price = Money("1.0", currency=checkout_line.get_total().currency)
        return TaxedMoney(price, price)

    def calculate_order_line_unit(self, order_line, previous_value):
        currency = order_line.unit_price.currency
        price = Money("1.0", currency)
        return TaxedMoney(price, price)

    def get_tax_rate_type_choices(self, previous_value):
        return [TaxType(code="123", description="abc")]

    def show_taxes_on_storefront(self, previous_value: bool) -> bool:
        return True

    def taxes_are_enabled(self, previous_value: bool) -> bool:
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
    PLUGIN_NAME = "PluginInactive"

    @classmethod
    def _get_default_configuration(cls):
        return {
            "name": "PluginInactive",
            "description": "Test plugin description_2",
            "active": False,
            "configuration": None,
        }


class ActivePlugin(BasePlugin):
    PLUGIN_NAME = "Plugin1"

    @classmethod
    def get_plugin_configuration(cls, queryset) -> "PluginConfiguration":
        qs = queryset.filter(name="Active")
        if qs.exists():
            return qs[0]
        defaults = {
            "name": "Active",
            "description": "Not working",
            "active": True,
            "configuration": [],
        }
        return PluginConfiguration.objects.create(**defaults)


class ActivePaymentGateway(BasePlugin):
    CLIENT_CONFIG = [{"field": "foo", "value": "bar"}]
    PLUGIN_NAME = "braintree"

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": "braintree",
            "description": "",
            "active": True,
            "configuration": None,
        }
        return defaults

    def process_payment(self, payment_information, previous_value):
        pass

    def get_payment_config(self, previous_value):
        return self.CLIENT_CONFIG


class InactivePaymentGateway(BasePlugin):
    PLUGIN_NAME = "stripe"

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": "stripe",
            "description": "",
            "active": False,
            "configuration": None,
        }
        return defaults

    def process_payment(self, payment_information, previous_value):
        pass
