from decimal import Decimal
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Union

import opentracing
from django.conf import settings
from django.utils.module_loading import import_string
from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ..checkout import base_calculations
from ..core.payments import PaymentInterface
from ..core.taxes import TaxType, quantize_price, zero_taxed_money
from ..discount import DiscountInfo
from .models import PluginConfiguration

if TYPE_CHECKING:
    # flake8: noqa
    from django.db.models.query import QuerySet
    from .base_plugin import BasePlugin, PluginConfigurationType
    from ..checkout.models import Checkout, CheckoutLine
    from ..product.models import Product, ProductType
    from ..account.models import Address, User
    from ..order.models import Fulfillment, OrderLine, Order
    from ..payment.interface import (
        PaymentData,
        TokenConfig,
        GatewayResponse,
        CustomerSource,
    )


class PluginsManager(PaymentInterface):
    """Base manager for handling plugins logic."""

    plugins: List["BasePlugin"] = []

    def __init__(self, plugins: List[str]):
        self.plugins = []
        all_configs = self._get_all_plugin_configs()
        for plugin_path in plugins:
            PluginClass = import_string(plugin_path)
            if PluginClass.PLUGIN_ID in all_configs:
                existing_config = all_configs[PluginClass.PLUGIN_ID]
                plugin_config = existing_config.configuration
                active = existing_config.active
            else:
                plugin_config = PluginClass.DEFAULT_CONFIGURATION
                active = PluginClass.get_default_active()
            self.plugins.append(PluginClass(configuration=plugin_config, active=active))

    def __run_method_on_plugins(
        self, method_name: str, default_value: Any, *args, **kwargs
    ):
        """Try to run a method with the given name on each declared plugin."""
        with opentracing.global_tracer().start_active_span(
            f"ExtensionsManager.{method_name}"
        ):
            value = default_value
            for plugin in self.plugins:
                value = self.__run_method_on_single_plugin(
                    plugin, method_name, value, *args, **kwargs
                )
            return value

    def __run_method_on_single_plugin(
        self,
        plugin: Optional["BasePlugin"],
        method_name: str,
        previous_value: Any,
        *args,
        **kwargs,
    ) -> Any:
        """Run method_name on plugin.

        Method will return value returned from plugin's
        method. If plugin doesn't have own implementation of expected method_name, it
        will return previous_value.
        """
        plugin_method = getattr(plugin, method_name, NotImplemented)
        if plugin_method == NotImplemented:
            return previous_value

        returned_value = plugin_method(*args, **kwargs, previous_value=previous_value)
        if returned_value == NotImplemented:
            return previous_value
        return returned_value

    def change_user_address(
        self, address: "Address", address_type: Optional[str], user: Optional["User"]
    ) -> "Address":
        default_value = address
        return self.__run_method_on_plugins(
            "change_user_address", default_value, address, address_type, user
        )

    def checkout_quantity_changed(self, checkout: "Checkout") -> None:
        self.__run_method_on_plugins("checkout_quantity_changed", None, checkout)

    def calculate_checkout_total(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLine"],
        discounts: Iterable[DiscountInfo],
    ) -> TaxedMoney:

        default_value = base_calculations.base_checkout_total(
            subtotal=self.calculate_checkout_subtotal(checkout, lines, discounts),
            shipping_price=self.calculate_checkout_shipping(checkout, lines, discounts),
            discount=checkout.discount,
            currency=checkout.currency,
        )
        return self.__run_method_on_plugins(
            "calculate_checkout_total", default_value, checkout, lines, discounts
        )

    def calculate_checkout_subtotal(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLine"],
        discounts: Iterable[DiscountInfo],
    ) -> TaxedMoney:
        line_totals = [
            self.calculate_checkout_line_total(line, discounts) for line in lines
        ]
        default_value = base_calculations.base_checkout_subtotal(
            line_totals, checkout.currency
        )
        return self.__run_method_on_plugins(
            "calculate_checkout_subtotal", default_value, checkout, lines, discounts
        )

    def calculate_checkout_shipping(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLine"],
        discounts: Iterable[DiscountInfo],
    ) -> TaxedMoney:
        default_value = base_calculations.base_checkout_shipping_price(checkout, lines)
        return self.__run_method_on_plugins(
            "calculate_checkout_shipping", default_value, checkout, lines, discounts
        )

    def calculate_order_shipping(self, order: "Order") -> TaxedMoney:
        if not order.shipping_method:
            return zero_taxed_money(order.currency)
        shipping_price = order.shipping_method.price
        default_value = quantize_price(
            TaxedMoney(net=shipping_price, gross=shipping_price),
            shipping_price.currency,
        )
        return self.__run_method_on_plugins(
            "calculate_order_shipping", default_value, order
        )

    def calculate_checkout_line_total(
        self, checkout_line: "CheckoutLine", discounts: Iterable[DiscountInfo]
    ):
        default_value = base_calculations.base_checkout_line_total(
            checkout_line, discounts
        )
        return self.__run_method_on_plugins(
            "calculate_checkout_line_total", default_value, checkout_line, discounts
        )

    def calculate_order_line_unit(self, order_line: "OrderLine") -> TaxedMoney:
        unit_price = order_line.unit_price
        default_value = quantize_price(unit_price, unit_price.currency)
        return self.__run_method_on_plugins(
            "calculate_order_line_unit", default_value, order_line
        )

    def get_tax_rate_type_choices(self) -> List[TaxType]:
        default_value: list = []
        return self.__run_method_on_plugins("get_tax_rate_type_choices", default_value)

    def show_taxes_on_storefront(self) -> bool:
        default_value = False
        return self.__run_method_on_plugins("show_taxes_on_storefront", default_value)

    def apply_taxes_to_product(
        self, product: "Product", price: Money, country: Country
    ):
        default_value = quantize_price(
            TaxedMoney(net=price, gross=price), price.currency
        )
        return self.__run_method_on_plugins(
            "apply_taxes_to_product", default_value, product, price, country
        )

    def apply_taxes_to_shipping(
        self, price: Money, shipping_address: "Address"
    ) -> TaxedMoney:
        default_value = quantize_price(
            TaxedMoney(net=price, gross=price), price.currency
        )
        return self.__run_method_on_plugins(
            "apply_taxes_to_shipping", default_value, price, shipping_address
        )

    def apply_taxes_to_shipping_price_range(self, prices: MoneyRange, country: Country):
        start = TaxedMoney(net=prices.start, gross=prices.start)
        stop = TaxedMoney(net=prices.stop, gross=prices.stop)
        default_value = quantize_price(
            TaxedMoneyRange(start=start, stop=stop), start.currency
        )
        return self.__run_method_on_plugins(
            "apply_taxes_to_shipping_price_range", default_value, prices, country
        )

    def preprocess_order_creation(
        self, checkout: "Checkout", discounts: Iterable[DiscountInfo]
    ):
        default_value = None
        return self.__run_method_on_plugins(
            "preprocess_order_creation", default_value, checkout, discounts
        )

    def customer_created(self, customer: "User"):
        default_value = None
        return self.__run_method_on_plugins("customer_created", default_value, customer)

    def product_created(self, product: "Product"):
        default_value = None
        return self.__run_method_on_plugins("product_created", default_value, product)

    def order_created(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins("order_created", default_value, order)

    def order_fully_paid(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins("order_fully_paid", default_value, order)

    def order_updated(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins("order_updated", default_value, order)

    def order_cancelled(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins("order_cancelled", default_value, order)

    def order_fulfilled(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins("order_fulfilled", default_value, order)

    def fulfillment_created(self, fulfillment: "Fulfillment"):
        default_value = None
        return self.__run_method_on_plugins(
            "fulfillment_created", default_value, fulfillment
        )

    def authorize_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        method_name = "authorize_payment"
        return self.__run_payment_method(gateway, method_name, payment_information)

    def capture_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        method_name = "capture_payment"
        return self.__run_payment_method(gateway, method_name, payment_information)

    def refund_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        method_name = "refund_payment"
        return self.__run_payment_method(gateway, method_name, payment_information)

    def void_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        method_name = "void_payment"
        return self.__run_payment_method(gateway, method_name, payment_information)

    def confirm_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        method_name = "confirm_payment"
        return self.__run_payment_method(gateway, method_name, payment_information)

    def process_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        method_name = "process_payment"
        return self.__run_payment_method(gateway, method_name, payment_information)

    def get_client_token(self, gateway, token_config: "TokenConfig") -> str:
        method_name = "get_client_token"
        default_value = None
        gtw = self.get_plugin(gateway)
        return self.__run_method_on_single_plugin(
            gtw, method_name, default_value, token_config=token_config
        )

    def list_payment_sources(
        self, gateway: str, customer_id: str
    ) -> List["CustomerSource"]:
        default_value: list = []
        gtw = self.get_plugin(gateway)
        if gtw is not None:
            return self.__run_method_on_single_plugin(
                gtw, "list_payment_sources", default_value, customer_id=customer_id
            )
        raise Exception(f"Payment plugin {gateway} is inaccessible!")

    def get_active_plugins(self, plugins=None) -> List["BasePlugin"]:
        if plugins is None:
            plugins = self.plugins
        return [plugin for plugin in plugins if plugin.active]

    def list_payment_plugin_names(self, active_only: bool = False) -> List[tuple]:
        payment_method = "process_payment"
        plugins = self.plugins
        if active_only:
            plugins = self.get_active_plugins()
        return [
            (plugin.PLUGIN_ID, plugin.PLUGIN_NAME)
            for plugin in plugins
            if payment_method in type(plugin).__dict__
        ]

    def list_payment_gateways(self, active_only: bool = True) -> List[dict]:
        payment_plugins = self.list_payment_plugin_names(active_only=active_only)
        return [
            {
                "id": plugin_id,
                "name": plugin_name,
                "config": self.__get_payment_config(plugin_id),
            }
            for plugin_id, plugin_name in payment_plugins
        ]

    def __get_payment_config(self, gateway: str) -> List[dict]:
        method_name = "get_payment_config"
        default_value: list = []
        gtw = self.get_plugin(gateway)
        return self.__run_method_on_single_plugin(gtw, method_name, default_value)

    def __run_payment_method(
        self,
        gateway: str,
        method_name: str,
        payment_information: "PaymentData",
        **kwargs,
    ) -> "GatewayResponse":
        default_value = None
        gtw = self.get_plugin(gateway)
        if gtw is not None:
            resp = self.__run_method_on_single_plugin(
                gtw,
                method_name,
                previous_value=default_value,
                payment_information=payment_information,
                **kwargs,
            )
            if resp is not None:
                return resp

        raise Exception(
            f"Payment plugin {gateway} for {method_name}"
            " payment method is inaccessible!"
        )

    def _get_all_plugin_configs(self):
        if not hasattr(self, "_plugin_configs"):
            self._plugin_configs = {
                pc.identifier: pc for pc in PluginConfiguration.objects.all()
            }
        return self._plugin_configs

    # FIXME these methods should be more generic

    def assign_tax_code_to_object_meta(
        self, obj: Union["Product", "ProductType"], tax_code: str
    ):
        default_value = None
        return self.__run_method_on_plugins(
            "assign_tax_code_to_object_meta", default_value, obj, tax_code
        )

    def get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType"]
    ) -> TaxType:
        default_value = TaxType(code="", description="")
        return self.__run_method_on_plugins(
            "get_tax_code_from_object_meta", default_value, obj
        )

    def get_tax_rate_percentage_value(
        self, obj: Union["Product", "ProductType"], country: Country
    ) -> Decimal:
        default_value = Decimal("0").quantize(Decimal("1."))
        return self.__run_method_on_plugins(
            "get_tax_rate_percentage_value", default_value, obj, country
        ).quantize(Decimal("1."))

    def save_plugin_configuration(self, plugin_id, cleaned_data: dict):
        for plugin in self.plugins:
            if plugin.PLUGIN_ID == plugin_id:
                plugin_configuration, _ = PluginConfiguration.objects.get_or_create(
                    identifier=plugin_id,
                    defaults={"configuration": plugin.configuration},
                )
                return plugin.save_plugin_configuration(
                    plugin_configuration, cleaned_data
                )

    def get_plugin(self, plugin_id: str) -> Optional["BasePlugin"]:
        for plugin in self.plugins:
            if plugin.PLUGIN_ID == plugin_id:
                return plugin
        return None


def get_plugins_manager(
    manager_path: str = None, plugins: List[str] = None
) -> PluginsManager:
    if not manager_path:
        manager_path = settings.PLUGINS_MANAGER
    if plugins is None:
        plugins = settings.PLUGINS
    manager = import_string(manager_path)
    return manager(plugins)
