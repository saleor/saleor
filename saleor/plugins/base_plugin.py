from copy import copy
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional, Union

from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from .models import PluginConfiguration

if TYPE_CHECKING:
    # flake8: noqa
    from ..core.taxes import TaxType
    from ..checkout.models import Checkout, CheckoutLine
    from ..discount import DiscountInfo
    from ..product.models import Product, ProductType
    from ..account.models import Address, User
    from ..order.models import Fulfillment, OrderLine, Order
    from ..payment.interface import GatewayResponse, PaymentData, CustomerSource


PluginConfigurationType = List[dict]


class ConfigurationTypeField:
    STRING = "String"
    BOOLEAN = "Boolean"
    SECRET = "Secret"
    PASSWORD = "Password"
    CHOICES = [
        (STRING, "Field is a String"),
        (BOOLEAN, "Field is a Boolean"),
        (SECRET, "Field is a Secret"),
        (PASSWORD, "Field is a Password"),
    ]


class BasePlugin:
    """Abstract class for storing all methods available for any plugin.

    All methods take previous_value parameter.
    previous_value contains a value calculated by the previous plugin in the queue.
    If the plugin is first, it will use default value calculated by the manager.
    """

    PLUGIN_NAME = ""
    PLUGIN_ID = ""
    PLUGIN_DESCRIPTION = ""
    CONFIG_STRUCTURE = None
    DEFAULT_CONFIGURATION = []
    DEFAULT_ACTIVE = False

    def __init__(self, *, configuration: PluginConfigurationType, active: bool):
        self.configuration = self.get_plugin_configuration(configuration)
        self.active = active

    def __str__(self):
        return self.PLUGIN_NAME

    def change_user_address(
        self,
        address: "Address",
        address_type: Optional[str],
        user: Optional["User"],
        previous_value: "Address",
    ) -> "Address":
        return NotImplemented

    def calculate_checkout_total(
        self,
        checkout: "Checkout",
        lines: List["CheckoutLine"],
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        """Calculate the total for checkout.

        Overwrite this method if you need to apply specific logic for the calculation
        of a checkout total. Return TaxedMoney.
        """
        return NotImplemented

    def calculate_checkout_subtotal(
        self,
        checkout: "Checkout",
        lines: List["CheckoutLine"],
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        """Calculate the subtotal for checkout.

        Overwrite this method if you need to apply specific logic for the calculation
        of a checkout subtotal. Return TaxedMoney.
        """
        return NotImplemented

    def calculate_checkout_shipping(
        self,
        checkout: "Checkout",
        lines: List["CheckoutLine"],
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        """Calculate the shipping costs for checkout.

        Overwrite this method if you need to apply specific logic for the calculation
        of shipping costs. Return TaxedMoney.
        """
        return NotImplemented

    def calculate_order_shipping(
        self, order: "Order", previous_value: TaxedMoney
    ) -> TaxedMoney:
        """Calculate the shipping costs for the order.

        Update shipping costs in the order in case of changes in shipping address or
        changes in draft order. Return TaxedMoney.
        """
        return NotImplemented

    def calculate_checkout_line_total(
        self,
        checkout_line: "CheckoutLine",
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        """Calculate checkout line total.

        Overwrite this method if you need to apply specific logic for the calculation
        of a checkout line total. Return TaxedMoney.
        """
        return NotImplemented

    def calculate_order_line_unit(
        self, order_line: "OrderLine", previous_value: TaxedMoney
    ) -> TaxedMoney:
        """Calculate order line unit price.

        Update order line unit price in the order in case of changes in draft order.
        Return TaxedMoney.
        Overwrite this method if you need to apply specific logic for the calculation
        of an order line unit price.
        """
        return NotImplemented

    def get_tax_rate_type_choices(
        self, previous_value: List["TaxType"]
    ) -> List["TaxType"]:
        """Return list of all tax categories.

        The returned list will be used to provide staff users with the possibility to
        assign tax categories to a product. It can be used by tax plugins to properly
        calculate taxes for products.
        Overwrite this method in case your plugin provides a list of tax categories.
        """
        return NotImplemented

    def show_taxes_on_storefront(self, previous_value: bool) -> bool:
        """Define if storefront should add info about taxes to the price.

        It is used only by the old storefront. The returned value determines if
        storefront should append info to the price about "including/excluding X% VAT".
        """
        return NotImplemented

    def apply_taxes_to_shipping_price_range(
        self, prices: MoneyRange, country: Country, previous_value: TaxedMoneyRange
    ) -> TaxedMoneyRange:
        """Provide the estimation of shipping costs based on country.

        It is used only by the old storefront in the cart view.
        """
        return NotImplemented

    def apply_taxes_to_shipping(
        self, price: Money, shipping_address: "Address", previous_value: TaxedMoney
    ) -> TaxedMoney:
        """Apply taxes to the shipping costs based on the shipping address.

        Overwrite this method if you want to show available shipping methods with
        taxes.
        """
        return NotImplemented

    def apply_taxes_to_product(
        self,
        product: "Product",
        price: Money,
        country: Country,
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        """Apply taxes to the product price based on the customer country.

        Overwrite this method if you want to show products with taxes.
        """
        return NotImplemented

    def preprocess_order_creation(
        self, checkout: "Checkout", discounts: List["DiscountInfo"], previous_value: Any
    ):
        """Trigger directly before order creation.

        Overwrite this method if you need to trigger specific logic before an order is
        created.
        """
        return NotImplemented

    def order_created(self, order: "Order", previous_value: Any):
        """Trigger when order is created.

        Overwrite this method if you need to trigger specific logic after an order is
        created.
        """
        return NotImplemented

    def assign_tax_code_to_object_meta(
        self, obj: Union["Product", "ProductType"], tax_code: str, previous_value: Any
    ):
        """Assign tax code dedicated to plugin."""
        return NotImplemented

    def get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType"], previous_value: "TaxType"
    ) -> "TaxType":
        """Return tax code from object meta."""
        return NotImplemented

    def get_tax_rate_percentage_value(
        self, obj: Union["Product", "ProductType"], country: Country, previous_value
    ) -> Decimal:
        """Return tax rate percentage value for a given tax rate type in a country.

        It is used only by the old storefront.
        """
        return NotImplemented

    def customer_created(self, customer: "User", previous_value: Any) -> Any:
        """Trigger when user is created.

        Overwrite this method if you need to trigger specific logic after a user is
        created.
        """
        return NotImplemented

    def product_created(self, product: "Product", previous_value: Any) -> Any:
        """Trigger when product is created.

        Overwrite this method if you need to trigger specific logic after a product is
        created.
        """
        return NotImplemented

    def order_fully_paid(self, order: "Order", previous_value: Any) -> Any:
        """Trigger when order is fully paid.

        Overwrite this method if you need to trigger specific logic when an order is
        fully paid.
        """
        return NotImplemented

    def order_updated(self, order: "Order", previous_value: Any) -> Any:
        """Trigger when order is updated.

        Overwrite this method if you need to trigger specific logic when an order is
        changed.
        """
        return NotImplemented

    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        """Trigger when order is cancelled.

        Overwrite this method if you need to trigger specific logic when an order is
        canceled.
        """
        return NotImplemented

    def order_fulfilled(self, order: "Order", previous_value: Any) -> Any:
        """Trigger when order is fulfilled.

        Overwrite this method if you need to trigger specific logic when an order is
        fulfilled.
        """
        return NotImplemented

    def fulfillment_created(
        self, fulfillment: "Fulfillment", previous_value: Any
    ) -> Any:
        """Trigger when fulfillemnt is created.

        Overwrite this method if you need to trigger specific logic when a fulfillment is
         created.
        """
        return NotImplemented

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return NotImplemented

    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return NotImplemented

    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return NotImplemented

    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return NotImplemented

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return NotImplemented

    def list_payment_sources(
        self, customer_id: str, previous_value
    ) -> List["CustomerSource"]:
        return NotImplemented

    def get_client_token(self, token_config, previous_value):
        return NotImplemented

    def get_payment_config(self, previous_value):
        return NotImplemented

    @classmethod
    def _update_config_items(
        cls, configuration_to_update: List[dict], current_config: List[dict]
    ):
        config_structure: dict = (
            cls.CONFIG_STRUCTURE if cls.CONFIG_STRUCTURE is not None else {}
        )
        for config_item in current_config:
            for config_item_to_update in configuration_to_update:
                config_item_name = config_item_to_update.get("name")
                if config_item["name"] == config_item_name:
                    new_value = config_item_to_update.get("value")
                    item_type = config_structure.get(config_item_name, {}).get("type")
                    if (
                        item_type == ConfigurationTypeField.BOOLEAN
                        and new_value
                        and not isinstance(new_value, bool)
                    ):
                        new_value = new_value.lower() == "true"
                    config_item.update([("value", new_value)])

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct.

        Raise django.core.exceptions.ValidationError otherwise.
        """
        return

    @classmethod
    def save_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", cleaned_data
    ):
        current_config = plugin_configuration.configuration
        configuration_to_update = cleaned_data.get("configuration")
        if configuration_to_update:
            cls._update_config_items(configuration_to_update, current_config)
        if "active" in cleaned_data:
            plugin_configuration.active = cleaned_data["active"]
        cls.validate_plugin_configuration(plugin_configuration)
        plugin_configuration.save()
        if plugin_configuration.configuration:
            # Let's add a translated descriptions and labels
            cls._append_config_structure(plugin_configuration.configuration)
        return plugin_configuration

    @classmethod
    def _append_config_structure(cls, configuration: PluginConfigurationType):
        """Append configuration structure to config from the database.

        Database stores "key: value" pairs, the definition of fields should be declared
        inside of the plugin. Based on this, the plugin will generate a structure of
        configuration with current values and provide access to it via API.
        """
        config_structure = getattr(cls, "CONFIG_STRUCTURE") or {}
        for configuration_field in configuration:

            structure_to_add = config_structure.get(configuration_field.get("name"))
            if structure_to_add:
                configuration_field.update(structure_to_add)

    @classmethod
    def _update_configuration_structure(cls, configuration: PluginConfigurationType):
        config_structure = getattr(cls, "CONFIG_STRUCTURE") or {}
        desired_config_keys = set(config_structure.keys())

        config = configuration or []
        configured_keys = set(d["name"] for d in config)
        missing_keys = desired_config_keys - configured_keys

        if not missing_keys:
            return

        default_config = cls.DEFAULT_CONFIGURATION
        if not default_config:
            return

        update_values = [copy(k) for k in default_config if k["name"] in missing_keys]
        config.extend(update_values)

    @classmethod
    def get_default_active(cls):
        return cls.DEFAULT_ACTIVE

    def get_plugin_configuration(
        self, configuration: PluginConfigurationType
    ) -> PluginConfigurationType:
        self._update_configuration_structure(configuration)
        if configuration:
            # Let's add a translated descriptions and labels
            self._append_config_structure(configuration)
        return configuration
