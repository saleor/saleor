from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Union

from django.conf import settings
from django.utils.module_loading import import_string
from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ..core.taxes import TaxType, quantize_price
from .models import PluginConfiguration

if TYPE_CHECKING:
    from .base_plugin import BasePlugin
    from ..checkout.models import Checkout, CheckoutLine
    from ..product.models import Product
    from ..account.models import Address
    from ..order.models import OrderLine, Order


class ExtensionsManager:
    """Base manager for handling plugins logic."""

    plugins = None

    def __init__(self, plugins: List[str]):
        self.plugins = []
        for plugin_path in plugins:
            plugin_class = import_string(plugin_path)
            self.plugins.append(plugin_class())

    def __run_method_on_plugins(
        self, method_name: str, default_value: Any, *args, **kwargs
    ):
        """Try to run a method with the given name on each declared plugin."""
        value = default_value
        for plugin in self.plugins:
            value = self.__run_method_on_single_plugin(
                plugin, method_name, value, *args, **kwargs
            )
        return value

    def __run_method_on_single_plugin(
        self,
        plugin: "BasePlugin",
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

    def calculate_checkout_total(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        total = checkout.get_total(discounts)
        default_value = quantize_price(
            TaxedMoney(net=total, gross=total), total.currency
        )
        return self.__run_method_on_plugins(
            "calculate_checkout_total", default_value, checkout, discounts
        )

    def calculate_checkout_subtotal(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        subtotal = checkout.get_subtotal(discounts)
        default_value = quantize_price(
            TaxedMoney(net=subtotal, gross=subtotal), subtotal.currency
        )
        return self.__run_method_on_plugins(
            "calculate_checkout_subtotal", default_value, checkout, discounts
        )

    def calculate_checkout_shipping(
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ) -> TaxedMoney:
        total = checkout.get_shipping_price()
        total = TaxedMoney(net=total, gross=total)
        default_value = quantize_price(total, total.currency)
        return self.__run_method_on_plugins(
            "calculate_checkout_shipping", default_value, checkout, discounts
        )

    def calculate_order_shipping(self, order: "Order") -> TaxedMoney:
        shipping_price = order.shipping_method.price
        default_value = quantize_price(
            TaxedMoney(net=shipping_price, gross=shipping_price),
            shipping_price.currency,
        )
        return self.__run_method_on_plugins(
            "calculate_order_shipping", default_value, order
        )

    def calculate_checkout_line_total(
        self, checkout_line: "CheckoutLine", discounts: List["DiscountInfo"]
    ):
        total = checkout_line.get_total(discounts)
        default_value = quantize_price(
            TaxedMoney(net=total, gross=total), total.currency
        )
        return self.__run_method_on_plugins(
            "calculate_checkout_line_total", default_value, checkout_line, discounts
        )

    def calculate_order_line_unit(self, order_line: "OrderLine"):
        unit_price = order_line.unit_price
        default_value = quantize_price(unit_price, unit_price.currency)
        return self.__run_method_on_plugins(
            "calculate_order_line_unit", default_value, order_line
        )

    def get_tax_rate_type_choices(self) -> List[TaxType]:
        default_value = []
        return self.__run_method_on_plugins("get_tax_rate_type_choices", default_value)

    def show_taxes_on_storefront(self) -> bool:
        default_value = False
        return self.__run_method_on_plugins("show_taxes_on_storefront", default_value)

    def taxes_are_enabled(self) -> bool:
        default_value = False
        return self.__run_method_on_plugins("taxes_are_enabled", default_value)

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
        self, checkout: "Checkout", discounts: List["DiscountInfo"]
    ):
        default_value = None
        return self.__run_method_on_plugins(
            "preprocess_order_creation", default_value, checkout, discounts
        )

    def postprocess_order_creation(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "postprocess_order_creation", default_value, order
        )

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

    def get_plugin_configuration(self, plugin_name) -> "PluginConfiguration":
        plugin_configurations_qs = PluginConfiguration.objects.all()
        for plugin in self.plugins:
            if plugin.PLUGIN_NAME == plugin_name:
                return plugin.get_plugin_configuration(plugin_configurations_qs)

    def get_plugin_configurations(self) -> List["PluginConfiguration"]:
        plugin_configurations = []
        plugin_configurations_qs = PluginConfiguration.objects.all()
        for plugin in self.plugins:
            plugin_configuration = plugin.get_plugin_configuration(
                plugin_configurations_qs
            )
            plugin_configurations.append(plugin_configuration)
        return plugin_configurations


def get_extensions_manager(
    manager_path: str = settings.EXTENSIONS_MANAGER,
    plugins: List[str] = settings.PLUGINS,
) -> ExtensionsManager:
    manager = import_string(manager_path)
    return manager(plugins)
