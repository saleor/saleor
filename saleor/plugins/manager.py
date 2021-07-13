from collections import defaultdict
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

import opentracing
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.module_loading import import_string
from django_countries.fields import Country
from prices import Money, TaxedMoney

from ..channel.models import Channel
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
    from ..product.models import Product, ProductType, ProductVariant
    from .base_plugin import BasePlugin


NotifyEventTypeChoice = str


class PluginsManager(PaymentInterface):
    """Base manager for handling plugins logic."""

    plugins_per_channel: Dict[str, List["BasePlugin"]] = {}
    global_plugins: List["BasePlugin"] = []
    all_plugins: List["BasePlugin"] = []

    def _load_plugin(
        self,
        PluginClass: Type["BasePlugin"],
        config,
        channel: Optional["Channel"] = None,
    ) -> "BasePlugin":

        if PluginClass.PLUGIN_ID in config:
            existing_config = config[PluginClass.PLUGIN_ID]
            plugin_config = existing_config.configuration
            active = existing_config.active
            channel = existing_config.channel
        else:
            plugin_config = PluginClass.DEFAULT_CONFIGURATION
            active = PluginClass.get_default_active()

        return PluginClass(configuration=plugin_config, active=active, channel=channel)

    def __init__(self, plugins: List[str]):
        with opentracing.global_tracer().start_active_span("PluginsManager.__init__"):
            self.plugins_per_channel = defaultdict(list)
            self.all_plugins = []
            (
                self._global_config,
                self._configs_per_channel,
            ) = self._get_all_plugin_configs()
            self.global_plugins = []
            channels = Channel.objects.all()
            for plugin_path in plugins:

                with opentracing.global_tracer().start_active_span(f"{plugin_path}"):
                    PluginClass = import_string(plugin_path)
                    if not getattr(PluginClass, "CONFIGURATION_PER_CHANNEL", False):
                        plugin = self._load_plugin(PluginClass, self._global_config)
                        self.global_plugins.append(plugin)
                        self.all_plugins.append(plugin)
                    else:
                        for channel in channels:
                            channel_configs = self._configs_per_channel.get(channel, {})
                            plugin = self._load_plugin(
                                PluginClass, channel_configs, channel
                            )
                            self.plugins_per_channel[channel.slug].append(plugin)
                            self.all_plugins.append(plugin)

            for channel in channels:
                self.plugins_per_channel[channel.slug].extend(self.global_plugins)

    def __run_method_on_plugins(
        self,
        method_name: str,
        default_value: Any,
        *args,
        channel_slug: Optional[str] = None,
        **kwargs
    ):
        """Try to run a method with the given name on each declared plugin."""
        with opentracing.global_tracer().start_active_span(
            f"PluginsManager.{method_name}"
        ):
            value = default_value
            plugins = self.get_plugins(channel_slug=channel_slug)

            for plugin in plugins:
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
                checkout_info, lines, address, discounts
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
                channel_slug=checkout_info.channel.slug,
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
                lines,
                line_info,
                address,
                discounts,
            )
            for line_info in lines
        ]
        currency = checkout_info.checkout.currency
        total = sum(line_totals, zero_taxed_money(currency))
        return quantize_price(
            total,
            checkout_info.checkout.currency,
        )

    def calculate_checkout_shipping(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
    ) -> TaxedMoney:
        default_value = base_calculations.base_checkout_shipping_price(
            checkout_info, lines
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_checkout_shipping",
                default_value,
                checkout_info,
                lines,
                address,
                discounts,
                channel_slug=checkout_info.channel.slug,
            ),
            checkout_info.checkout.currency,
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
                "calculate_order_shipping",
                default_value,
                order,
                channel_slug=order.channel.slug,
            ),
            order.currency,
        )

    def get_checkout_shipping_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        shipping_price: TaxedMoney,
    ):
        default_value = base_calculations.base_tax_rate(shipping_price)
        return self.__run_method_on_plugins(
            "get_checkout_shipping_tax_rate",
            default_value,
            checkout_info,
            lines,
            address,
            discounts,
            channel_slug=checkout_info.channel.slug,
        ).quantize(Decimal(".0001"))

    def get_order_shipping_tax_rate(self, order: "Order", shipping_price: TaxedMoney):
        default_value = base_calculations.base_tax_rate(shipping_price)
        return self.__run_method_on_plugins(
            "get_order_shipping_tax_rate",
            default_value,
            order,
            channel_slug=order.channel.slug,
        ).quantize(Decimal(".0001"))

    def calculate_checkout_line_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
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
                lines,
                checkout_line_info,
                address,
                discounts,
                channel_slug=checkout_info.channel.slug,
            ),
            checkout_info.checkout.currency,
        )

    def calculate_order_line_total(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
    ):
        default_value = base_calculations.base_order_line_total(order_line)
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_order_line_total",
                default_value,
                order,
                order_line,
                variant,
                product,
            ),
            order.currency,
        )

    def calculate_checkout_line_unit_price(
        self,
        total_line_price: TaxedMoney,
        quantity: int,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
    ):
        default_value = base_calculations.base_checkout_line_unit_price(
            total_line_price, quantity
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "calculate_checkout_line_unit_price",
                default_value,
                checkout_info,
                lines,
                checkout_line_info,
                address,
                discounts,
                channel_slug=checkout_info.channel.slug,
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
                channel_slug=order.channel.slug,
            ),
            order_line.currency,
        )

    def get_checkout_line_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        unit_price: TaxedMoney,
    ) -> Decimal:
        default_value = base_calculations.base_tax_rate(unit_price)
        return self.__run_method_on_plugins(
            "get_checkout_line_tax_rate",
            default_value,
            checkout_info,
            lines,
            checkout_line_info,
            address,
            discounts,
            channel_slug=checkout_info.channel.slug,
        ).quantize(Decimal(".0001"))

    def get_order_line_tax_rate(
        self,
        order: "Order",
        product: "Product",
        variant: "ProductVariant",
        address: Optional["Address"],
        unit_price: TaxedMoney,
    ) -> Decimal:
        default_value = base_calculations.base_tax_rate(unit_price)
        return self.__run_method_on_plugins(
            "get_order_line_tax_rate",
            default_value,
            order,
            product,
            variant,
            address,
            channel_slug=order.channel.slug,
        ).quantize(Decimal(".0001"))

    def get_tax_rate_type_choices(self) -> List[TaxType]:
        default_value: list = []
        return self.__run_method_on_plugins("get_tax_rate_type_choices", default_value)

    def show_taxes_on_storefront(self) -> bool:
        default_value = False
        return self.__run_method_on_plugins("show_taxes_on_storefront", default_value)

    def apply_taxes_to_product(
        self, product: "Product", price: Money, country: Country, channel_slug: str
    ):
        default_value = quantize_price(
            TaxedMoney(net=price, gross=price), price.currency
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "apply_taxes_to_product",
                default_value,
                product,
                price,
                country,
                channel_slug=channel_slug,
            ),
            price.currency,
        )

    def apply_taxes_to_shipping(
        self, price: Money, shipping_address: "Address", channel_slug: str
    ) -> TaxedMoney:
        default_value = quantize_price(
            TaxedMoney(net=price, gross=price), price.currency
        )
        return quantize_price(
            self.__run_method_on_plugins(
                "apply_taxes_to_shipping",
                default_value,
                price,
                shipping_address,
                channel_slug=channel_slug,
            ),
            price.currency,
        )

    def preprocess_order_creation(
        self,
        checkout_info: "CheckoutInfo",
        discounts: Iterable[DiscountInfo],
        lines: Optional[Iterable["CheckoutLineInfo"]] = None,
    ):
        default_value = None
        return self.__run_method_on_plugins(
            "preprocess_order_creation",
            default_value,
            checkout_info,
            discounts,
            lines,
            channel_slug=checkout_info.channel.slug,
        )

    def customer_created(self, customer: "User"):
        default_value = None
        return self.__run_method_on_plugins("customer_created", default_value, customer)

    def customer_updated(self, customer: "User"):
        default_value = None
        return self.__run_method_on_plugins("customer_updated", default_value, customer)

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

    def product_variant_created(self, product_variant: "ProductVariant"):
        default_value = None
        return self.__run_method_on_plugins(
            "product_variant_created", default_value, product_variant
        )

    def product_variant_updated(self, product_variant: "ProductVariant"):
        default_value = None
        return self.__run_method_on_plugins(
            "product_variant_updated", default_value, product_variant
        )

    def product_variant_deleted(self, product_variant: "ProductVariant"):
        default_value = None
        return self.__run_method_on_plugins(
            "product_variant_deleted", default_value, product_variant
        )

    def order_created(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "order_created", default_value, order, channel_slug=order.channel.slug
        )

    def order_confirmed(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "order_confirmed", default_value, order, channel_slug=order.channel.slug
        )

    def invoice_request(
        self, order: "Order", invoice: "Invoice", number: Optional[str]
    ):
        default_value = None
        return self.__run_method_on_plugins(
            "invoice_request",
            default_value,
            order,
            invoice,
            number,
            channel_slug=order.channel.slug,
        )

    def invoice_delete(self, invoice: "Invoice"):
        default_value = None
        channel_slug = invoice.order.channel.slug if invoice.order else None
        return self.__run_method_on_plugins(
            "invoice_delete",
            default_value,
            invoice,
            channel_slug=channel_slug,
        )

    def invoice_sent(self, invoice: "Invoice", email: str):
        default_value = None
        channel_slug = invoice.order.channel.slug if invoice.order else None
        return self.__run_method_on_plugins(
            "invoice_sent",
            default_value,
            invoice,
            email,
            channel_slug=channel_slug,
        )

    def order_fully_paid(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "order_fully_paid", default_value, order, channel_slug=order.channel.slug
        )

    def order_updated(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "order_updated", default_value, order, channel_slug=order.channel.slug
        )

    def order_cancelled(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "order_cancelled", default_value, order, channel_slug=order.channel.slug
        )

    def order_fulfilled(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "order_fulfilled", default_value, order, channel_slug=order.channel.slug
        )

    def fulfillment_created(self, fulfillment: "Fulfillment"):
        default_value = None
        return self.__run_method_on_plugins(
            "fulfillment_created",
            default_value,
            fulfillment,
            channel_slug=fulfillment.order.channel.slug,
        )

    def checkout_created(self, checkout: "Checkout"):
        default_value = None
        return self.__run_method_on_plugins(
            "checkout_created",
            default_value,
            checkout,
            channel_slug=checkout.channel.slug,
        )

    def checkout_updated(self, checkout: "Checkout"):
        default_value = None
        return self.__run_method_on_plugins(
            "checkout_updated",
            default_value,
            checkout,
            channel_slug=checkout.channel.slug,
        )

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
        self, gateway, payment_data: dict, channel_slug: str
    ) -> Optional["InitializedPaymentResponse"]:
        method_name = "initialize_payment"
        default_value = None
        gtw = self.get_plugin(gateway, channel_slug)
        if not gtw:
            return None

        return self.__run_method_on_single_plugin(
            gtw,
            method_name,
            previous_value=default_value,
            payment_data=payment_data,
        )

    def authorize_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        return self.__run_payment_method(
            gateway, "authorize_payment", payment_information, channel_slug=channel_slug
        )

    def capture_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        return self.__run_payment_method(
            gateway, "capture_payment", payment_information, channel_slug=channel_slug
        )

    def refund_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        return self.__run_payment_method(
            gateway, "refund_payment", payment_information, channel_slug=channel_slug
        )

    def void_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        return self.__run_payment_method(
            gateway, "void_payment", payment_information, channel_slug=channel_slug
        )

    def confirm_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        return self.__run_payment_method(
            gateway, "confirm_payment", payment_information, channel_slug=channel_slug
        )

    def process_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        return self.__run_payment_method(
            gateway, "process_payment", payment_information, channel_slug=channel_slug
        )

    def token_is_required_as_payment_input(
        self, gateway: str, channel_slug: str
    ) -> bool:
        method_name = "token_is_required_as_payment_input"
        default_value = True
        gtw = self.get_plugin(gateway, channel_slug=channel_slug)
        if gtw is not None:
            return self.__run_method_on_single_plugin(
                gtw,
                method_name,
                previous_value=default_value,
            )
        return default_value

    def get_client_token(
        self,
        gateway,
        token_config: "TokenConfig",
        channel_slug: str,
    ) -> str:
        method_name = "get_client_token"
        default_value = None
        gtw = self.get_plugin(gateway, channel_slug=channel_slug)
        return self.__run_method_on_single_plugin(
            gtw, method_name, default_value, token_config=token_config
        )

    def list_payment_sources(
        self,
        gateway: str,
        customer_id: str,
        channel_slug: str,
    ) -> List["CustomerSource"]:
        default_value: list = []
        gtw = self.get_plugin(gateway, channel_slug=channel_slug)
        if gtw is not None:
            return self.__run_method_on_single_plugin(
                gtw, "list_payment_sources", default_value, customer_id=customer_id
            )
        raise Exception(f"Payment plugin {gateway} is inaccessible!")

    def get_plugins(
        self, channel_slug: Optional[str] = None, active_only=False
    ) -> List["BasePlugin"]:
        """Return list of plugins for a given channel."""
        if channel_slug:
            plugins = self.plugins_per_channel[channel_slug]
        else:
            plugins = self.all_plugins

        if active_only:
            plugins = [plugin for plugin in plugins if plugin.active]
        return plugins

    def list_payment_gateways(
        self,
        currency: Optional[str] = None,
        checkout: Optional["Checkout"] = None,
        channel_slug: Optional[str] = None,
        active_only: bool = True,
    ) -> List["PaymentGateway"]:
        channel_slug = checkout.channel.slug if checkout else channel_slug
        plugins = self.get_plugins(channel_slug=channel_slug, active_only=active_only)
        payment_plugins = [
            plugin for plugin in plugins if "process_payment" in type(plugin).__dict__
        ]

        # if currency is given return only gateways which support given currency
        gateways = []
        for plugin in payment_plugins:
            gateways.extend(
                plugin.get_payment_gateways(
                    currency=currency, checkout=checkout, previous_value=None
                )
            )
        return gateways

    def list_external_authentications(self, active_only: bool = True) -> List[dict]:
        auth_basic_method = "external_obtain_access_tokens"
        plugins = self.get_plugins(active_only=active_only)
        return [
            {"id": plugin.PLUGIN_ID, "name": plugin.PLUGIN_NAME}
            for plugin in plugins
            if auth_basic_method in type(plugin).__dict__
        ]

    def __run_payment_method(
        self,
        gateway: str,
        method_name: str,
        payment_information: "PaymentData",
        channel_slug: str,
        **kwargs,
    ) -> "GatewayResponse":
        default_value = None
        plugin = self.get_plugin(gateway, channel_slug)
        if plugin is not None:
            resp = self.__run_method_on_single_plugin(
                plugin,
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
                plugin_configurations = PluginConfiguration.objects.prefetch_related(
                    "channel"
                ).all()
                self._plugin_configs_per_channel = defaultdict(dict)
                self._global_plugin_configs = {}
                for pc in plugin_configurations:
                    channel = pc.channel
                    if channel is None:
                        self._global_plugin_configs[pc.identifier] = pc
                    else:
                        self._plugin_configs_per_channel[channel][pc.identifier] = pc
            return self._global_plugin_configs, self._plugin_configs_per_channel

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

    def save_plugin_configuration(
        self, plugin_id, channel_slug: Optional[str], cleaned_data: dict
    ):
        if channel_slug:
            plugins = self.get_plugins(channel_slug=channel_slug)
            channel = Channel.objects.filter(slug=channel_slug).first()
            if not channel:
                return None
        else:
            channel = None
            plugins = self.global_plugins

        for plugin in plugins:
            if plugin.PLUGIN_ID == plugin_id:
                plugin_configuration, _ = PluginConfiguration.objects.get_or_create(
                    identifier=plugin_id,
                    channel=channel,
                    defaults={"configuration": plugin.configuration},
                )
                configuration = plugin.save_plugin_configuration(
                    plugin_configuration, cleaned_data
                )
                configuration.name = plugin.PLUGIN_NAME
                configuration.description = plugin.PLUGIN_DESCRIPTION
                plugin.active = configuration.active
                plugin.configuration = configuration.configuration
                return configuration

    def get_plugin(
        self, plugin_id: str, channel_slug: Optional[str] = None
    ) -> Optional["BasePlugin"]:
        plugins = self.get_plugins(channel_slug=channel_slug)
        for plugin in plugins:
            if plugin.check_plugin_id(plugin_id):
                return plugin
        return None

    def fetch_taxes_data(self) -> bool:
        default_value = False
        return self.__run_method_on_plugins("fetch_taxes_data", default_value)

    def webhook_endpoint_without_channel(
        self, request: WSGIRequest, plugin_id: str
    ) -> HttpResponse:
        # This should be removed in 3.0.0-a.25 as we want to give a possibility to have
        # no downtime between RCs
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

    def webhook(
        self, request: WSGIRequest, plugin_id: str, channel_slug: Optional[str] = None
    ) -> HttpResponse:
        split_path = request.path.split(plugin_id, maxsplit=1)
        path = None
        if len(split_path) == 2:
            path = split_path[1]

        default_value = HttpResponseNotFound()
        plugin = self.get_plugin(plugin_id, channel_slug=channel_slug)
        if not plugin:
            return default_value

        if not plugin.active:
            return default_value

        if plugin.CONFIGURATION_PER_CHANNEL and not channel_slug:
            return HttpResponseNotFound(
                "Incorrect endpoint. Use /plugins/channel/<channel_slug>/"
                f"{plugin.PLUGIN_ID}/"
            )

        return self.__run_method_on_single_plugin(
            plugin, "webhook", default_value, request, path
        )

    def notify(
        self,
        event: "NotifyEventTypeChoice",
        payload: dict,
        channel_slug: Optional[str] = None,
    ):
        default_value = None
        return self.__run_method_on_plugins(
            "notify", default_value, event, payload, channel_slug=channel_slug
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
