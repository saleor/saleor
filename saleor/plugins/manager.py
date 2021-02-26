from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, Union

import opentracing
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.module_loading import import_string
from django_countries.fields import Country
from prices import Money, TaxedMoney

from ..checkout import base_calculations
from ..core.payments import PaymentInterface
from ..core.prices import quantize_price
from ..core.taxes import TaxType, zero_taxed_money
from ..discount import DiscountInfo
from .base_plugin import ExternalAccessTokens
from .models import PluginConfiguration

if TYPE_CHECKING:
    # flake8: noqa
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..checkout.models import Checkout
    from ..invoice.models import Invoice
    from ..order.models import Fulfillment, Order, OrderLine
    from ..page.models import Page
    from ..payment.interface import (
        CustomerSource,
        GatewayResponse,
        InitializedPaymentResponse,
        PaymentData,
        PaymentGateway,
        TokenConfig,
    )
    from ..product.models import (
        Collection,
        Product,
        ProductType,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from .base_plugin import BasePlugin


class PluginsManager(PaymentInterface):
    """Base manager for handling plugins logic."""

    plugins: List["BasePlugin"] = []

    def __init__(self, plugins: List[str]):
        with opentracing.global_tracer().start_active_span("PluginsManager.__init__"):
            self.plugins = []
            all_configs = self._get_all_plugin_configs()
            for plugin_path in plugins:
                with opentracing.global_tracer().start_active_span(f"{plugin_path}"):
                    PluginClass = import_string(plugin_path)
                    if PluginClass.PLUGIN_ID in all_configs:
                        existing_config = all_configs[PluginClass.PLUGIN_ID]
                        plugin_config = existing_config.configuration
                        active = existing_config.active
                    else:
                        plugin_config = PluginClass.DEFAULT_CONFIGURATION
                        active = PluginClass.get_default_active()
                    plugin = PluginClass(configuration=plugin_config, active=active)
                self.plugins.append(plugin)

    def __run_method_on_plugins(
        self, method_name: str, default_value: Any, *args, **kwargs
    ):
        """Try to run a method with the given name on each declared plugin."""
        with opentracing.global_tracer().start_active_span(
            f"PluginsManager.{method_name}"
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
        plugin_id = getattr(plugin, "PLUGIN_ID", "")
        with opentracing.global_tracer().start_active_span(
            f"{plugin_id}.{method_name}"
        ):
            plugin_method = getattr(plugin, method_name, NotImplemented)
            if plugin_method == NotImplemented:
                return previous_value

            returned_value = plugin_method(
                *args, **kwargs, previous_value=previous_value
            )
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

    def calculate_checkout_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
    ) -> TaxedMoney:

        default_value = base_calculations.base_checkout_total(
            subtotal=self.calculate_checkout_subtotal(
                checkout_info, lines, address, discounts
            ),
            shipping_price=self.calculate_checkout_shipping(
                checkout_info.checkout, lines, address, discounts
            ),
            discount=checkout_info.checkout.discount,
            currency=checkout_info.checkout.currency,
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_checkout_total",
                default_value,
                checkout_info,
                lines,
                address,
                discounts,
            ),
            checkout_info.checkout.currency,
        )

    def calculate_checkout_subtotal(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
    ) -> TaxedMoney:
        line_totals = [
            self.calculate_checkout_line_total(
                checkout_info,
                line_info,
                address,
                discounts,
            )
            for line_info in lines
        ]
        default_value = base_calculations.base_checkout_subtotal(
            line_totals, checkout_info.checkout.currency
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_checkout_subtotal",
                default_value,
                checkout_info,
                lines,
                address,
                discounts,
            ),
            checkout_info.checkout.currency,
        )

    def calculate_checkout_shipping(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
    ) -> TaxedMoney:
        default_value = base_calculations.base_checkout_shipping_price(checkout, lines)
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_checkout_shipping",
                default_value,
                checkout,
                lines,
                address,
                discounts,
            ),
            checkout.currency,
        )

    def calculate_order_shipping(self, order: "Order") -> TaxedMoney:
        if not order.shipping_method:
            return zero_taxed_money(order.currency)
        shipping_price = order.shipping_method.channel_listings.get(
            channel_id=order.channel_id
        ).price
        default_value = quantize_price(
            TaxedMoney(net=shipping_price, gross=shipping_price),
            shipping_price.currency,
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_order_shipping", default_value, order
            ),
            order.currency,
        )

    def get_checkout_shipping_tax_rate(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        shipping_price: TaxedMoney,
    ):
        default_value = base_calculations.base_tax_rate(shipping_price)
        return self.__run_method_on_plugins(
            "get_checkout_shipping_tax_rate",
            default_value,
            checkout,
            lines,
            address,
            discounts,
        ).quantize(Decimal(".0001"))

    def get_order_shipping_tax_rate(self, order: "Order", shipping_price: TaxedMoney):
        default_value = base_calculations.base_tax_rate(shipping_price)
        return self.__run_method_on_plugins(
            "get_order_shipping_tax_rate", default_value, order
        ).quantize(Decimal(".0001"))

    def calculate_checkout_line_total(
        self,
        checkout_info: "CheckoutInfo",
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
    ):
        default_value = base_calculations.base_checkout_line_total(
            checkout_line_info,
            checkout_info.channel,
            discounts,
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_checkout_line_total",
                default_value,
                checkout_info,
                checkout_line_info,
                address,
                discounts,
            ),
            checkout_info.checkout.currency,
        )

    def calculate_checkout_line_unit_price(
        self,
        total_line_price: TaxedMoney,
        quantity: int,
        checkout: "Checkout",
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        channel: "Channel",
    ):
        default_value = base_calculations.base_checkout_line_unit_price(
            total_line_price, quantity
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_checkout_line_unit_price",
                default_value,
                checkout,
                checkout_line_info,
                address,
                discounts,
                channel,
            ),
            total_line_price.currency,
        )

    def calculate_order_line_unit(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
    ) -> TaxedMoney:
        unit_price = order_line.unit_price
        default_value = quantize_price(unit_price, unit_price.currency)
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_order_line_unit",
                default_value,
                order,
                order_line,
                variant,
                product,
            ),
            order_line.currency,
        )

    def get_checkout_line_tax_rate(
        self,
        checkout: "Checkout",
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        unit_price: TaxedMoney,
    ) -> Decimal:
        default_value = base_calculations.base_tax_rate(unit_price)
        return self.__run_method_on_plugins(
            "get_checkout_line_tax_rate",
            default_value,
            checkout,
            checkout_line_info,
            address,
            discounts,
        ).quantize(Decimal(".0001"))

    def get_order_line_tax_rate(
        self,
        order: "Order",
        product: "Product",
        address: Optional["Address"],
        unit_price: TaxedMoney,
    ) -> Decimal:
        default_value = base_calculations.base_tax_rate(unit_price)
        return self.__run_method_on_plugins(
            "get_order_line_tax_rate", default_value, order, product, address
        ).quantize(Decimal(".0001"))

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
        return quantize_price(
            self.__run_method_on_plugins(
                "apply_taxes_to_product", default_value, product, price, country
            ),
            price.currency,
        )

    def apply_taxes_to_shipping(
        self, price: Money, shipping_address: "Address"
    ) -> TaxedMoney:
        default_value = quantize_price(
            TaxedMoney(net=price, gross=price), price.currency
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "apply_taxes_to_shipping", default_value, price, shipping_address
            ),
            price.currency,
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

    def product_updated(self, product: "Product"):
        default_value = None
        return self.__run_method_on_plugins("product_updated", default_value, product)

    def product_deleted(self, product: "Product", variants: List[int]):
        default_value = None
        return self.__run_method_on_plugins(
            "product_deleted", default_value, product, variants
        )

    def order_created(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins("order_created", default_value, order)

    def order_confirmed(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins("order_confirmed", default_value, order)

    def invoice_request(
        self, order: "Order", invoice: "Invoice", number: Optional[str]
    ):
        default_value = None
        return self.__run_method_on_plugins(
            "invoice_request", default_value, order, invoice, number
        )

    def invoice_delete(self, invoice: "Invoice"):
        default_value = None
        return self.__run_method_on_plugins("invoice_delete", default_value, invoice)

    def invoice_sent(self, invoice: "Invoice", email: str):
        default_value = None
        return self.__run_method_on_plugins(
            "invoice_sent", default_value, invoice, email
        )

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

    def checkout_created(self, checkout: "Checkout"):
        default_value = None
        return self.__run_method_on_plugins("checkout_created", default_value, checkout)

    def checkout_updated(self, checkout: "Checkout"):
        default_value = None
        return self.__run_method_on_plugins("checkout_updated", default_value, checkout)

    def page_created(self, page: "Page"):
        default_value = None
        return self.__run_method_on_plugins("page_created", default_value, page)

    def page_updated(self, page: "Page"):
        default_value = None
        return self.__run_method_on_plugins("page_updated", default_value, page)

    def page_deleted(self, page: "Page"):
        default_value = None
        return self.__run_method_on_plugins("page_deleted", default_value, page)

    def initialize_payment(
        self, gateway, payment_data: dict
    ) -> Optional["InitializedPaymentResponse"]:
        method_name = "initialize_payment"
        default_value = None
        gtw = self.get_plugin(gateway)
        if not gtw:
            return None

        return self.__run_method_on_single_plugin(
            gtw,
            method_name,
            previous_value=default_value,
            payment_data=payment_data,
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

    def token_is_required_as_payment_input(self, gateway) -> bool:
        method_name = "token_is_required_as_payment_input"
        default_value = True
        gtw = self.get_plugin(gateway)
        if gtw is not None:
            return self.__run_method_on_single_plugin(
                gtw,
                method_name,
                previous_value=default_value,
            )
        return default_value

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

    def list_payment_plugin(self, active_only: bool = False) -> Dict[str, "BasePlugin"]:
        payment_method = "process_payment"
        plugins = self.plugins
        if active_only:
            plugins = self.get_active_plugins()
        return {
            plugin.PLUGIN_ID: plugin
            for plugin in plugins
            if payment_method in type(plugin).__dict__
        }

    def list_payment_gateways(
        self, currency: Optional[str] = None, active_only: bool = True
    ) -> List["PaymentGateway"]:
        payment_plugins = self.list_payment_plugin(active_only=active_only)
        # if currency is given return only gateways which support given currency
        gateways = []
        for plugin in payment_plugins.values():
            gateway = plugin.get_payment_gateway(currency=currency, previous_value=None)
            if gateway:
                gateways.append(gateway)
        return gateways

    def list_external_authentications(self, active_only: bool = True) -> List[dict]:
        plugins = self.plugins
        auth_basic_method = "external_obtain_access_tokens"
        if active_only:
            plugins = self.get_active_plugins()
        return [
            {"id": plugin.PLUGIN_ID, "name": plugin.PLUGIN_NAME}
            for plugin in plugins
            if auth_basic_method in type(plugin).__dict__
        ]

    def checkout_available_payment_gateways(
        self,
        checkout: "Checkout",
    ) -> List["PaymentGateway"]:
        payment_plugins = self.list_payment_plugin(active_only=True)
        gateways = []
        for plugin in payment_plugins.values():
            gateway = plugin.get_payment_gateway_for_checkout(
                checkout, previous_value=None
            )
            if gateway:
                gateways.append(gateway)
        return gateways

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
        with opentracing.global_tracer().start_active_span("_get_all_plugin_configs"):
            if not hasattr(self, "_plugin_configs"):
                self._plugin_configs = {
                    pc.identifier: pc for pc in PluginConfiguration.objects.all()
                }
            return self._plugin_configs

    # FIXME these methods should be more generic

    def assign_tax_code_to_object_meta(
        self, obj: Union["Product", "ProductType"], tax_code: Optional[str]
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
                configuration = plugin.save_plugin_configuration(
                    plugin_configuration, cleaned_data
                )
                configuration.name = plugin.PLUGIN_NAME
                configuration.description = plugin.PLUGIN_DESCRIPTION
                return configuration

    def get_plugin(self, plugin_id: str) -> Optional["BasePlugin"]:
        for plugin in self.plugins:
            if plugin.PLUGIN_ID == plugin_id:
                return plugin
        return None

    def fetch_taxes_data(self) -> bool:
        default_value = False
        return self.__run_method_on_plugins("fetch_taxes_data", default_value)

    def webhook(self, request: WSGIRequest, plugin_id: str) -> HttpResponse:
        split_path = request.path.split(plugin_id, maxsplit=1)
        path = None
        if len(split_path) == 2:
            path = split_path[1]

        default_value = HttpResponseNotFound()
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return default_value
        return self.__run_method_on_single_plugin(
            plugin, "webhook", default_value, request, path
        )

    def external_obtain_access_tokens(
        self, plugin_id: str, data: dict, request: WSGIRequest
    ) -> Optional["ExternalAccessTokens"]:
        """Obtain access tokens from authentication plugin."""
        default_value = ExternalAccessTokens()
        plugin = self.get_plugin(plugin_id)
        return self.__run_method_on_single_plugin(
            plugin, "external_obtain_access_tokens", default_value, data, request
        )

    def external_authentication_url(
        self, plugin_id: str, data: dict, request: WSGIRequest
    ) -> dict:
        """Handle authentication request."""
        default_value = {}  # type: ignore
        plugin = self.get_plugin(plugin_id)
        return self.__run_method_on_single_plugin(
            plugin, "external_authentication_url", default_value, data, request
        )

    def external_refresh(
        self, plugin_id: str, data: dict, request: WSGIRequest
    ) -> Optional["ExternalAccessTokens"]:
        """Handle authentication refresh request."""
        default_value = ExternalAccessTokens()
        plugin = self.get_plugin(plugin_id)
        return self.__run_method_on_single_plugin(
            plugin, "external_refresh", default_value, data, request
        )

    def authenticate_user(self, request: WSGIRequest) -> Optional["User"]:
        """Authenticate user which should be assigned to the request."""
        default_value = None
        return self.__run_method_on_plugins("authenticate_user", default_value, request)

    def external_logout(self, plugin_id: str, data: dict, request: WSGIRequest) -> dict:
        """Logout the user."""
        default_value: Dict[str, str] = {}
        plugin = self.get_plugin(plugin_id)
        return self.__run_method_on_single_plugin(
            plugin, "external_logout", default_value, data, request
        )

    def external_verify(
        self, plugin_id: str, data: dict, request: WSGIRequest
    ) -> Tuple[Optional["User"], dict]:
        """Verify the provided authentication data."""
        default_data: Dict[str, str] = dict()
        default_user: Optional["User"] = None
        default_value = default_user, default_data
        plugin = self.get_plugin(plugin_id)
        return self.__run_method_on_single_plugin(
            plugin, "external_verify", default_value, data, request
        )


def get_plugins_manager() -> PluginsManager:
    with opentracing.global_tracer().start_active_span("get_plugins_manager"):
        return PluginsManager(settings.PLUGINS)
