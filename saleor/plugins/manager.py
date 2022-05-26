from collections import defaultdict
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
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
from graphene import Mutation
from graphql import GraphQLError, ResolveInfo
from graphql.execution import ExecutionResult
from prices import Money, TaxedMoney

from ..channel.models import Channel
from ..checkout import base_calculations
from ..checkout.interface import CheckoutTaxedPricesData
from ..core.models import EventDelivery
from ..core.payments import PaymentInterface
from ..core.prices import quantize_price
from ..core.taxes import TaxType, zero_money, zero_taxed_money
from ..discount import DiscountInfo, VoucherType
from ..order.interface import OrderTaxedPricesData
from .base_plugin import ExcludedShippingMethod, ExternalAccessTokens
from .models import PluginConfiguration

if TYPE_CHECKING:
    # flake8: noqa
    from ..account.models import Address, User
    from ..app.models import App
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..checkout.models import Checkout
    from ..core.middleware import Requestor
    from ..discount.models import Sale, Voucher
    from ..giftcard.models import GiftCard
    from ..invoice.models import Invoice
    from ..menu.models import Menu, MenuItem
    from ..order.models import Fulfillment, Order, OrderLine
    from ..page.models import Page
    from ..payment.interface import (
        CustomerSource,
        GatewayResponse,
        InitializedPaymentResponse,
        PaymentData,
        PaymentGateway,
        TokenConfig,
        TransactionActionData,
    )
    from ..product.models import (
        Category,
        Collection,
        Product,
        ProductType,
        ProductVariant,
    )
    from ..shipping.interface import ShippingMethodData
    from ..shipping.models import ShippingMethod, ShippingZone
    from ..translation.models import Translation
    from ..warehouse.models import Stock, Warehouse
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
        db_configs_map: dict,
        channel: Optional["Channel"] = None,
        requestor_getter=None,
    ) -> "BasePlugin":
        db_config = None
        if PluginClass.PLUGIN_ID in db_configs_map:
            db_config = db_configs_map[PluginClass.PLUGIN_ID]
            plugin_config = db_config.configuration
            active = db_config.active
            channel = db_config.channel
        else:
            plugin_config = PluginClass.DEFAULT_CONFIGURATION
            active = PluginClass.get_default_active()

        return PluginClass(
            configuration=plugin_config,
            active=active,
            channel=channel,
            requestor_getter=requestor_getter,
            db_config=db_config,
        )

    def __init__(self, plugins: List[str], requestor_getter=None):
        with opentracing.global_tracer().start_active_span("PluginsManager.__init__"):
            self.all_plugins = []
            self.global_plugins = []
            self.plugins_per_channel = defaultdict(list)

            global_db_configs, channel_db_configs = self._get_db_plugin_configs()
            channels = Channel.objects.all()

            for plugin_path in plugins:
                with opentracing.global_tracer().start_active_span(f"{plugin_path}"):
                    PluginClass = import_string(plugin_path)
                    if not getattr(PluginClass, "CONFIGURATION_PER_CHANNEL", False):
                        plugin = self._load_plugin(
                            PluginClass,
                            global_db_configs,
                            requestor_getter=requestor_getter,
                        )
                        self.global_plugins.append(plugin)
                        self.all_plugins.append(plugin)
                    else:
                        for channel in channels:
                            channel_configs = channel_db_configs.get(channel, {})
                            plugin = self._load_plugin(
                                PluginClass, channel_configs, channel, requestor_getter
                            )
                            self.plugins_per_channel[channel.slug].append(plugin)
                            self.all_plugins.append(plugin)

            for channel in channels:
                self.plugins_per_channel[channel.slug].extend(self.global_plugins)

    def _get_db_plugin_configs(self):
        with opentracing.global_tracer().start_active_span("_get_db_plugin_configs"):
            qs = (
                PluginConfiguration.objects.all()
                .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
                .prefetch_related("channel")
            )
            channel_configs = defaultdict(dict)
            global_configs = {}
            for db_plugin_config in qs:
                channel = db_plugin_config.channel
                if channel is None:
                    global_configs[db_plugin_config.identifier] = db_plugin_config
                else:
                    channel_configs[channel][
                        db_plugin_config.identifier
                    ] = db_plugin_config
            return global_configs, channel_configs

    def __run_method_on_plugins(
        self,
        method_name: str,
        default_value: Any,
        *args,
        channel_slug: Optional[str] = None,
        **kwargs
    ):
        """Try to run a method with the given name on each declared active plugin."""
        value = default_value
        plugins = self.get_plugins(channel_slug=channel_slug, active_only=True)
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
        returned_value = plugin_method(
            *args, **kwargs, previous_value=previous_value
        )  # type:ignore
        if returned_value == NotImplemented:
            return previous_value
        return returned_value

    def check_payment_balance(self, details: dict, channel_slug: str) -> dict:
        return self.__run_method_on_plugins(
            "check_payment_balance", None, details, channel_slug=channel_slug
        )

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
        currency = checkout_info.checkout.currency
        default_value = base_calculations.base_checkout_total(
            subtotal=self.calculate_checkout_subtotal(
                checkout_info, lines, address, discounts
            ),
            shipping_price=self.calculate_checkout_shipping(
                checkout_info, lines, address, discounts
            ),
            discount=checkout_info.checkout.discount,
            currency=currency,
        )

        if default_value <= zero_taxed_money(currency):
            return quantize_price(
                default_value,
                currency,
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
            currency,
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
            ).price_with_discounts
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
        default_value = base_calculations.base_checkout_delivery_price(
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
        channel_listing = order.shipping_method.channel_listings.filter(
            channel_id=order.channel_id
        ).first()
        if not channel_listing:
            return zero_taxed_money(order.currency)
        shipping_price = channel_listing.price
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
    ) -> CheckoutTaxedPricesData:
        default_value = base_calculations.base_checkout_line_total(
            checkout_line_info,
            checkout_info.channel,
            discounts,
        )
        line_total = self.__run_method_on_plugins(
            "calculate_checkout_line_total",
            default_value,
            checkout_info,
            lines,
            checkout_line_info,
            address,
            discounts,
            channel_slug=checkout_info.channel.slug,
        )
        currency = checkout_info.checkout.currency
        line_total.price_with_sale = quantize_price(
            line_total.price_with_sale, currency
        )
        line_total.price_with_discounts = quantize_price(
            line_total.price_with_discounts, currency
        )
        line_total.undiscounted_price = quantize_price(
            line_total.undiscounted_price, currency
        )
        return line_total

    def calculate_order_line_total(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
    ) -> OrderTaxedPricesData:
        default_value = base_calculations.base_order_line_total(order_line)
        line_total = self.__run_method_on_plugins(
            "calculate_order_line_total",
            default_value,
            order,
            order_line,
            variant,
            product,
            channel_slug=order.channel.slug,
        )
        currency = order_line.currency
        line_total.price_with_discounts = quantize_price(
            line_total.price_with_discounts, currency
        )
        line_total.undiscounted_price = quantize_price(
            line_total.undiscounted_price, currency
        )
        return line_total

    def calculate_checkout_line_unit_price(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
    ) -> CheckoutTaxedPricesData:
        default_value = base_calculations.base_checkout_line_unit_price(
            checkout_line_info, checkout_info.channel, discounts
        )
        line_unit = self.__run_method_on_plugins(
            "calculate_checkout_line_unit_price",
            default_value,
            checkout_info,
            lines,
            checkout_line_info,
            address,
            discounts,
            channel_slug=checkout_info.channel.slug,
        )
        currency = checkout_info.checkout.currency
        line_unit.price_with_sale = quantize_price(line_unit.price_with_sale, currency)
        line_unit.price_with_discounts = quantize_price(
            line_unit.price_with_discounts, currency
        )
        line_unit.undiscounted_price = quantize_price(
            line_unit.undiscounted_price, currency
        )
        return line_unit

    def calculate_order_line_unit(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
    ) -> OrderTaxedPricesData:
        default_value = OrderTaxedPricesData(
            undiscounted_price=TaxedMoney(
                order_line.undiscounted_base_unit_price,
                order_line.undiscounted_base_unit_price,
            ),
            price_with_discounts=TaxedMoney(
                order_line.base_unit_price,
                order_line.base_unit_price,
            ),
        )
        currency = order_line.currency
        line_unit = self.__run_method_on_plugins(
            "calculate_order_line_unit",
            default_value,
            order,
            order_line,
            variant,
            product,
            channel_slug=order.channel.slug,
        )
        line_unit.price_with_discounts = quantize_price(
            line_unit.price_with_discounts, currency
        )
        line_unit.undiscounted_price = quantize_price(
            line_unit.undiscounted_price, currency
        )
        return line_unit

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

    def collection_created(self, collection: "Collection"):
        default_value = None
        return self.__run_method_on_plugins(
            "collection_created", default_value, collection
        )

    def collection_updated(self, collection: "Collection"):
        default_value = None
        return self.__run_method_on_plugins(
            "collection_updated", default_value, collection
        )

    def collection_deleted(self, collection: "Collection"):
        default_value = None
        return self.__run_method_on_plugins(
            "collection_deleted", default_value, collection
        )

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
            "product_variant_deleted",
            default_value,
            product_variant,
        )

    def product_variant_out_of_stock(self, stock: "Stock"):
        default_value = None
        self.__run_method_on_plugins(
            "product_variant_out_of_stock", default_value, stock
        )

    def product_variant_back_in_stock(self, stock: "Stock"):
        default_value = None
        self.__run_method_on_plugins(
            "product_variant_back_in_stock", default_value, stock
        )

    def order_created(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "order_created", default_value, order, channel_slug=order.channel.slug
        )

    def event_delivery_retry(self, event_delivery: "EventDelivery"):
        default_value = None
        return self.__run_method_on_plugins(
            "event_delivery_retry", default_value, event_delivery
        )

    def order_confirmed(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "order_confirmed", default_value, order, channel_slug=order.channel.slug
        )

    def draft_order_created(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "draft_order_created", default_value, order, channel_slug=order.channel.slug
        )

    def draft_order_updated(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "draft_order_updated", default_value, order, channel_slug=order.channel.slug
        )

    def draft_order_deleted(self, order: "Order"):
        default_value = None
        return self.__run_method_on_plugins(
            "draft_order_deleted", default_value, order, channel_slug=order.channel.slug
        )

    def sale_created(self, sale: "Sale", current_catalogue):
        default_value = None
        return self.__run_method_on_plugins(
            "sale_created", default_value, sale, current_catalogue
        )

    def sale_deleted(self, sale: "Sale", previous_catalogue):
        default_value = None
        return self.__run_method_on_plugins(
            "sale_deleted", default_value, sale, previous_catalogue
        )

    def sale_updated(self, sale: "Sale", previous_catalogue, current_catalogue):
        default_value = None
        return self.__run_method_on_plugins(
            "sale_updated", default_value, sale, previous_catalogue, current_catalogue
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

    def fulfillment_canceled(self, fulfillment: "Fulfillment"):
        default_value = None
        return self.__run_method_on_plugins(
            "fulfillment_canceled",
            default_value,
            fulfillment,
            channel_slug=fulfillment.order.channel.slug,
        )

    def tracking_number_updated(self, fulfillment: "Fulfillment"):
        default_value = None
        return self.__run_method_on_plugins(
            "tracking_number_updated",
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

    def transaction_action_request(
        self, payment_data: "TransactionActionData", channel_slug: str
    ):
        default_value = None
        return self.__run_method_on_plugins(
            "transaction_action_request",
            default_value,
            payment_data,
            channel_slug=channel_slug,
        )

    def app_installed(self, app: "App"):
        default_value = None
        return self.__run_method_on_plugins("app_installed", default_value, app)

    def app_updated(self, app: "App"):
        default_value = None
        return self.__run_method_on_plugins("app_updated", default_value, app)

    def app_deleted(self, app: "App"):
        default_value = None
        return self.__run_method_on_plugins("app_deleted", default_value, app)

    def app_status_changed(self, app: "App"):
        default_value = None
        return self.__run_method_on_plugins("app_status_changed", default_value, app)

    def category_created(self, category: "Category"):
        default_value = None
        return self.__run_method_on_plugins("category_created", default_value, category)

    def category_updated(self, category: "Category"):
        default_value = None
        return self.__run_method_on_plugins("category_updated", default_value, category)

    def category_deleted(self, category: "Category"):
        default_value = None
        return self.__run_method_on_plugins("category_deleted", default_value, category)

    def channel_created(self, channel: "Channel"):
        default_value = None
        return self.__run_method_on_plugins("channel_created", default_value, channel)

    def channel_updated(self, channel: "Channel"):
        default_value = None
        return self.__run_method_on_plugins("channel_updated", default_value, channel)

    def channel_deleted(self, channel: "Channel"):
        default_value = None
        return self.__run_method_on_plugins("channel_deleted", default_value, channel)

    def channel_status_changed(self, channel: "Channel"):
        default_value = None
        return self.__run_method_on_plugins(
            "channel_status_changed", default_value, channel
        )

    def gift_card_created(self, gift_card: "GiftCard"):
        default_value = None
        return self.__run_method_on_plugins(
            "gift_card_created", default_value, gift_card
        )

    def gift_card_updated(self, gift_card: "GiftCard"):
        default_value = None
        return self.__run_method_on_plugins(
            "gift_card_updated", default_value, gift_card
        )

    def gift_card_deleted(self, gift_card: "GiftCard"):
        default_value = None
        return self.__run_method_on_plugins(
            "gift_card_deleted", default_value, gift_card
        )

    def gift_card_status_changed(self, gift_card: "GiftCard"):
        default_value = None
        return self.__run_method_on_plugins(
            "gift_card_status_changed", default_value, gift_card
        )

    def menu_created(self, menu: "Menu"):
        default_value = None
        return self.__run_method_on_plugins("menu_created", default_value, menu)

    def menu_updated(self, menu: "Menu"):
        default_value = None
        return self.__run_method_on_plugins("menu_updated", default_value, menu)

    def menu_deleted(self, menu: "Menu"):
        default_value = None
        return self.__run_method_on_plugins("menu_deleted", default_value, menu)

    def menu_item_created(self, menu_item: "MenuItem"):
        default_value = None
        return self.__run_method_on_plugins(
            "menu_item_created", default_value, menu_item
        )

    def menu_item_updated(self, menu_item: "MenuItem"):
        default_value = None
        return self.__run_method_on_plugins(
            "menu_item_updated", default_value, menu_item
        )

    def menu_item_deleted(self, menu_item: "MenuItem"):
        default_value = None
        return self.__run_method_on_plugins(
            "menu_item_deleted", default_value, menu_item
        )

    def shipping_price_created(self, shipping_method: "ShippingMethod"):
        default_value = None
        return self.__run_method_on_plugins(
            "shipping_price_created", default_value, shipping_method
        )

    def shipping_price_updated(self, shipping_method: "ShippingMethod"):
        default_value = None
        return self.__run_method_on_plugins(
            "shipping_price_updated", default_value, shipping_method
        )

    def shipping_price_deleted(self, shipping_method: "ShippingMethod"):
        default_value = None
        return self.__run_method_on_plugins(
            "shipping_price_deleted", default_value, shipping_method
        )

    def shipping_zone_created(self, shipping_zone: "ShippingZone"):
        default_value = None
        return self.__run_method_on_plugins(
            "shipping_zone_created", default_value, shipping_zone
        )

    def shipping_zone_updated(self, shipping_zone: "ShippingZone"):
        default_value = None
        return self.__run_method_on_plugins(
            "shipping_zone_updated", default_value, shipping_zone
        )

    def shipping_zone_deleted(self, shipping_zone: "ShippingZone"):
        default_value = None
        return self.__run_method_on_plugins(
            "shipping_zone_deleted", default_value, shipping_zone
        )

    def warehouse_created(self, warehouse: "Warehouse"):
        default_value = None
        return self.__run_method_on_plugins(
            "warehouse_created", default_value, warehouse
        )

    def warehouse_updated(self, warehouse: "Warehouse"):
        default_value = None
        return self.__run_method_on_plugins(
            "warehouse_updated", default_value, warehouse
        )

    def warehouse_deleted(self, warehouse: "Warehouse"):
        default_value = None
        return self.__run_method_on_plugins(
            "warehouse_deleted", default_value, warehouse
        )

    def voucher_created(self, voucher: "Voucher"):
        default_value = None
        return self.__run_method_on_plugins("voucher_created", default_value, voucher)

    def voucher_updated(self, voucher: "Voucher"):
        default_value = None
        return self.__run_method_on_plugins("voucher_updated", default_value, voucher)

    def voucher_deleted(self, voucher: "Voucher"):
        default_value = None
        return self.__run_method_on_plugins("voucher_deleted", default_value, voucher)

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

    def translation_created(self, translation: "Translation"):
        default_value = None
        return self.__run_method_on_plugins(
            "translation_created", default_value, translation
        )

    def translation_updated(self, translation: "Translation"):
        default_value = None
        return self.__run_method_on_plugins(
            "translation_updated", default_value, translation
        )

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

    def list_shipping_methods_for_checkout(
        self,
        checkout: "Checkout",
        channel_slug: Optional[str] = None,
        active_only: bool = True,
    ) -> List["ShippingMethodData"]:
        channel_slug = checkout.channel.slug if checkout else channel_slug
        plugins = self.get_plugins(channel_slug=channel_slug, active_only=active_only)
        shipping_plugins = [
            plugin
            for plugin in plugins
            if hasattr(plugin, "get_shipping_methods_for_checkout")
        ]

        shipping_methods = []
        for plugin in shipping_plugins:
            shipping_methods.extend(
                # https://github.com/python/mypy/issues/9975
                getattr(plugin, "get_shipping_methods_for_checkout")(checkout, None)
            )
        return shipping_methods

    def get_shipping_method(
        self,
        shipping_method_id: str,
        checkout: Optional["Checkout"] = None,
        channel_slug: Optional[str] = None,
    ):
        if checkout:
            methods = {
                method.id: method
                for method in self.list_shipping_methods_for_checkout(
                    checkout=checkout, channel_slug=channel_slug
                )
            }
            return methods.get(shipping_method_id)
        return None

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
        plugin_id: Optional[str] = None,
    ):
        default_value = None
        if plugin_id:
            plugin = self.get_plugin(plugin_id, channel_slug=channel_slug)
            return self.__run_method_on_single_plugin(
                plugin=plugin,
                method_name="notify",
                previous_value=default_value,
                event=event,
                payload=payload,
            )
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

    def excluded_shipping_methods_for_order(
        self,
        order: "Order",
        available_shipping_methods: List["ShippingMethodData"],
    ) -> List[ExcludedShippingMethod]:
        return self.__run_method_on_plugins(
            "excluded_shipping_methods_for_order",
            [],
            order,
            available_shipping_methods,
        )

    def excluded_shipping_methods_for_checkout(
        self,
        checkout: "Checkout",
        available_shipping_methods: List["ShippingMethodData"],
    ) -> List[ExcludedShippingMethod]:
        return self.__run_method_on_plugins(
            "excluded_shipping_methods_for_checkout",
            [],
            checkout,
            available_shipping_methods,
        )

    def perform_mutation(
        self, mutation_cls: Mutation, root, info: ResolveInfo, data: dict
    ) -> Optional[Union[ExecutionResult, GraphQLError]]:
        """Invoke before each mutation is executed.

        This allows to trigger specific logic before the mutation is executed
        but only once the permissions are checked.

        Returns one of:
            - null if the execution shall continue
            - graphql.GraphQLError
            - graphql.execution.ExecutionResult
        """
        return self.__run_method_on_plugins(
            "perform_mutation",
            default_value=None,
            mutation_cls=mutation_cls,
            root=root,
            info=info,
            data=data,
        )

    def is_event_active_for_any_plugin(
        self, event: str, channel_slug: Optional[str] = None
    ) -> bool:
        """Check if any plugin supports defined event."""
        plugins = (
            self.plugins_per_channel[channel_slug] if channel_slug else self.all_plugins
        )
        only_active_plugins = [plugin for plugin in plugins if plugin.active]
        return any([plugin.is_event_active(event) for plugin in only_active_plugins])


def get_plugins_manager(
    requestor_getter: Optional[Callable[[], "Requestor"]] = None
) -> PluginsManager:
    with opentracing.global_tracer().start_active_span("get_plugins_manager"):
        return PluginsManager(settings.PLUGINS, requestor_getter)
