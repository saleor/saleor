from copy import copy
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Optional, Tuple, Union

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.utils.functional import SimpleLazyObject
from django_countries.fields import Country
from graphene import Mutation
from graphql import GraphQLError, ResolveInfo
from graphql.execution import ExecutionResult
from prices import Money, TaxedMoney
from promise.promise import Promise

from ..checkout.interface import CheckoutTaxedPricesData
from ..core.models import EventDelivery
from ..payment.interface import (
    CustomerSource,
    GatewayResponse,
    InitializedPaymentResponse,
    PaymentData,
    PaymentGateway,
    TransactionActionData,
)
from .models import PluginConfiguration

if TYPE_CHECKING:
    # flake8: noqa
    from ..account.models import Address, User
    from ..app.models import App
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..checkout.models import Checkout
    from ..core.middleware import Requestor
    from ..core.notify_events import NotifyEventType
    from ..core.taxes import TaxType
    from ..discount import DiscountInfo, Voucher
    from ..discount.models import Sale
    from ..giftcard.models import GiftCard
    from ..graphql.discount.mutations import NodeCatalogueInfo
    from ..invoice.models import Invoice
    from ..menu.models import Menu, MenuItem
    from ..order.models import Fulfillment, Order, OrderLine
    from ..page.models import Page
    from ..product.models import (
        Category,
        Collection,
        Product,
        ProductType,
        ProductVariant,
    )
    from ..shipping.interface import ShippingMethodData
    from ..shipping.models import ShippingMethod, ShippingZone

PluginConfigurationType = List[dict]
NoneType = type(None)
RequestorOrLazyObject = Union[SimpleLazyObject, "Requestor"]


class ConfigurationTypeField:
    STRING = "String"
    MULTILINE = "Multiline"
    BOOLEAN = "Boolean"
    SECRET = "Secret"
    SECRET_MULTILINE = "SecretMultiline"
    PASSWORD = "Password"
    OUTPUT = "OUTPUT"
    CHOICES = [
        (STRING, "Field is a String"),
        (MULTILINE, "Field is a Multiline"),
        (BOOLEAN, "Field is a Boolean"),
        (SECRET, "Field is a Secret"),
        (PASSWORD, "Field is a Password"),
        (SECRET_MULTILINE, "Field is a Secret multiline"),
        (OUTPUT, "Field is a read only"),
    ]


@dataclass
class ExternalAccessTokens:
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    csrf_token: Optional[str] = None
    user: Optional["User"] = None


@dataclass
class ExcludedShippingMethod:
    id: str
    reason: Optional[str]


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
    CONFIGURATION_PER_CHANNEL = True
    DEFAULT_CONFIGURATION = []
    DEFAULT_ACTIVE = False
    HIDDEN = False

    @classmethod
    def check_plugin_id(cls, plugin_id: str) -> bool:
        """Check if given plugin_id matches with the PLUGIN_ID of this plugin."""
        return cls.PLUGIN_ID == plugin_id

    def __init__(
        self,
        *,
        configuration: PluginConfigurationType,
        active: bool,
        channel: Optional["Channel"] = None,
        requestor_getter: Optional[Callable[[], "Requestor"]] = None,
        db_config: Optional["PluginConfiguration"] = None
    ):
        self.configuration = self.get_plugin_configuration(configuration)
        self.active = active
        self.channel = channel
        self.requestor: Optional[RequestorOrLazyObject] = (
            SimpleLazyObject(requestor_getter) if requestor_getter else requestor_getter
        )
        self.db_config = db_config

    def __str__(self):
        return self.PLUGIN_NAME

    #  Trigger when app is created.
    #
    #  Overwrite this method if you need to trigger specific logic after an app is
    #  created.
    app_created: Callable[["App", None], None]

    #  Trigger when app is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after an app is
    #  deleted.
    app_deleted: Callable[["App", None], None]

    #  Trigger when app is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after an app is
    #  updated.
    app_updated: Callable[["App", None], None]

    #  Trigger when channel status is changed.
    #
    #  Overwrite this method if you need to trigger specific logic after an app
    #  status is changed.
    app_status_changed: Callable[["App", None], None]

    #  Apply taxes to the product price based on the customer country.
    #
    #  Overwrite this method if you want to show products with taxes.
    apply_taxes_to_product: Callable[
        ["Product", Money, Country, TaxedMoney], TaxedMoney
    ]

    #  Assign tax code dedicated to plugin.
    assign_tax_code_to_object_meta: Callable[
        [Union["Product", "ProductType"], Union[str, NoneType], Any], Any
    ]

    #  Authenticate user which should be assigned to the request.
    #
    #  Overwrite this method if the plugin handles authentication flow.
    authenticate_user: Callable[
        [WSGIRequest, Optional["User"]], Union["User", NoneType]
    ]

    authorize_payment: Callable[["PaymentData", Any], GatewayResponse]

    #  Calculate checkout line total.
    #
    #  Overwrite this method if you need to apply specific logic for the calculation
    #  of a checkout line total. Return TaxedMoney.
    calculate_checkout_line_total: Callable[
        [
            "CheckoutInfo",
            List["CheckoutLineInfo"],
            "CheckoutLineInfo",
            Union["Address", NoneType],
            Iterable["DiscountInfo"],
            TaxedMoney,
        ],
        CheckoutTaxedPricesData,
    ]

    #  Calculate checkout line unit price.
    calculate_checkout_line_unit_price: Callable[
        [
            "CheckoutInfo",
            List["CheckoutLineInfo"],
            "CheckoutLineInfo",
            Union["Address", NoneType],
            Iterable["DiscountInfo"],
            Any,
        ],
        CheckoutTaxedPricesData,
    ]

    #  Calculate the shipping costs for checkout.
    #
    #  Overwrite this method if you need to apply specific logic for the calculation
    #  of shipping costs. Return TaxedMoney.
    calculate_checkout_shipping: Callable[
        [
            "CheckoutInfo",
            List["CheckoutLineInfo"],
            Union["Address", NoneType],
            List["DiscountInfo"],
            TaxedMoney,
        ],
        TaxedMoney,
    ]

    #  Calculate the total for checkout.
    #
    #  Overwrite this method if you need to apply specific logic for the calculation
    #  of a checkout total. Return TaxedMoney.
    calculate_checkout_total: Callable[
        [
            "CheckoutInfo",
            List["CheckoutLineInfo"],
            Union["Address", NoneType],
            List["DiscountInfo"],
            TaxedMoney,
        ],
        TaxedMoney,
    ]

    #  Calculate order line total.
    #
    #  Overwrite this method if you need to apply specific logic for the calculation
    #  of a order line total. Return TaxedMoney.
    calculate_order_line_total: Callable[
        ["Order", "OrderLine", "ProductVariant", "Product", TaxedMoney], TaxedMoney
    ]

    #  Calculate order line unit price.
    #
    #  Update order line unit price in the order in case of changes in draft order.
    #  Return TaxedMoney.
    #  Overwrite this method if you need to apply specific logic for the calculation
    #  of an order line unit price.
    calculate_order_line_unit: Callable[
        ["Order", "OrderLine", "ProductVariant", "Product", TaxedMoney], TaxedMoney
    ]

    #  Calculate the shipping costs for the order.
    #
    #  Update shipping costs in the order in case of changes in shipping address or
    #  changes in draft order. Return TaxedMoney.
    calculate_order_shipping: Callable[["Order", TaxedMoney], TaxedMoney]

    capture_payment: Callable[["PaymentData", Any], GatewayResponse]

    #  Trigger when category is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a category is
    #  created.
    category_created: Callable[["Category", None], None]

    #  Trigger when category is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a category is
    #  deleted.
    category_deleted: Callable[["Category", None], None]

    #  Trigger when category is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a category is
    #  updated.
    category_updated: Callable[["Category", None], None]

    #  Trigger when channel is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a channel is
    #  created.
    channel_created: Callable[["Channel", None], None]

    #  Trigger when channel is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a channel is
    #  deleted.
    channel_deleted: Callable[["Channel", None], None]

    #  Trigger when channel is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a channel is
    #  updated.
    channel_updated: Callable[["Channel", None], None]

    #  Trigger when channel status is changed.
    #
    #  Overwrite this method if you need to trigger specific logic after a channel
    #  status is changed.
    channel_status_changed: Callable[["Channel", None], None]

    change_user_address: Callable[
        ["Address", Union[str, NoneType], Union["User", NoneType], "Address"], "Address"
    ]

    #  Retrieves the balance remaining on a shopper's gift card
    check_payment_balance: Callable[[dict, str], dict]

    #  Trigger when checkout is created.
    #
    #  Overwrite this method if you need to trigger specific logic when a checkout is
    #  created.
    checkout_created: Callable[["Checkout", Any], Any]

    #  Trigger when checkout is updated.
    #
    #  Overwrite this method if you need to trigger specific logic when a checkout is
    #  updated.
    checkout_updated: Callable[["Checkout", Any], Any]

    #  Trigger when collection is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a collection is
    #  created.
    collection_created: Callable[["Collection", Any], Any]

    #  Trigger when collection is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a collection is
    #  deleted.
    collection_deleted: Callable[["Collection", Any], Any]

    #  Trigger when collection is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a collection is
    #  updated.
    collection_updated: Callable[["Collection", Any], Any]

    confirm_payment: Callable[["PaymentData", Any], GatewayResponse]

    #  Trigger when user is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a user is
    #  created.
    customer_created: Callable[["User", Any], Any]

    #  Trigger when user is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a user is
    #  updated.
    customer_updated: Callable[["User", Any], Any]

    #  Handle authentication request.
    #
    #  Overwrite this method if the plugin handles authentication flow.
    external_authentication_url: Callable[[dict, WSGIRequest, dict], dict]

    #  Handle logout request.
    #
    #  Overwrite this method if the plugin handles logout flow.
    external_logout: Callable[[dict, WSGIRequest, dict], Any]

    #  Handle authentication request responsible for obtaining access tokens.
    #
    #  Overwrite this method if the plugin handles authentication flow.
    external_obtain_access_tokens: Callable[
        [dict, WSGIRequest, ExternalAccessTokens], ExternalAccessTokens
    ]

    #  Handle authentication refresh request.
    #
    #  Overwrite this method if the plugin handles authentication flow and supports
    #  refreshing the access.
    external_refresh: Callable[
        [dict, WSGIRequest, ExternalAccessTokens], ExternalAccessTokens
    ]

    #  Verify the provided authentication data.
    #
    #  Overwrite this method if the plugin should validate the authentication data.
    external_verify: Callable[
        [dict, WSGIRequest, Tuple[Union["User", NoneType], dict]],
        Tuple[Union["User", NoneType], dict],
    ]

    #  Triggered when ShopFetchTaxRates mutation is called.
    fetch_taxes_data: Callable[[Any], Any]

    #  Trigger when fulfillemnt is created.
    #
    #  Overwrite this method if you need to trigger specific logic when a fulfillment is
    #  created.
    fulfillment_created: Callable[["Fulfillment", Any], Any]

    #  Trigger when fulfillemnt is cancelled.
    #  Overwrite this method if you need to trigger specific logic when a fulfillment is
    #  cancelled.
    fulfillment_canceled: Callable[["Fulfillment", Any], Any]

    get_checkout_line_tax_rate: Callable[
        [
            "CheckoutInfo",
            List["CheckoutLineInfo"],
            "CheckoutLineInfo",
            Union["Address", NoneType],
            Iterable["DiscountInfo"],
            Decimal,
        ],
        Decimal,
    ]

    get_checkout_shipping_tax_rate: Callable[
        [
            "CheckoutInfo",
            Iterable["CheckoutLineInfo"],
            Union["Address", NoneType],
            Iterable["DiscountInfo"],
            Any,
        ],
        Any,
    ]

    get_client_token: Callable[[Any, Any], Any]

    get_order_line_tax_rate: Callable[
        ["Order", "Product", "ProductVariant", Union["Address", NoneType], Decimal],
        Decimal,
    ]

    get_order_shipping_tax_rate: Callable[["Order", Any], Any]
    get_payment_config: Callable[[Any], Any]

    get_shipping_methods_for_checkout: Callable[
        ["Checkout", Any], List["ShippingMethodData"]
    ]

    get_supported_currencies: Callable[[Any], Any]

    #  Return tax code from object meta.
    get_tax_code_from_object_meta: Callable[
        [Union["Product", "ProductType"], "TaxType"], "TaxType"
    ]

    #  Return tax rate percentage value for a given tax rate type in a country.
    #
    #  It is used only by the old storefront.
    get_tax_rate_percentage_value: Callable[
        [Union["Product", "ProductType"], Country, Any], Decimal
    ]

    #  Return list of all tax categories.
    #
    #  The returned list will be used to provide staff users with the possibility to
    #  assign tax categories to a product. It can be used by tax plugins to properly
    #  calculate taxes for products.
    #  Overwrite this method in case your plugin provides a list of tax categories.
    get_tax_rate_type_choices: Callable[[List["TaxType"]], List["TaxType"]]

    #  Trigger when gift card is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a gift card is
    #  created.
    gift_card_created: Callable[["GiftCard", None], None]

    #  Trigger when gift card is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a gift card is
    #  deleted.
    gift_card_deleted: Callable[["GiftCard", None], None]

    #  Trigger when gift card is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a gift card is
    #  updated.
    gift_card_updated: Callable[["GiftCard", None], None]

    #  Trigger when gift card status is changed.
    #
    #  Overwrite this method if you need to trigger specific logic after a gift card
    #  status is changed.
    gift_card_status_changed: Callable[["GiftCard", None], None]

    initialize_payment: Callable[[dict], InitializedPaymentResponse]

    #  Trigger before invoice is deleted.
    #
    #  Perform any extra logic before the invoice gets deleted.
    #  Note there is no need to run invoice.delete() as it will happen in mutation.
    invoice_delete: Callable[["Invoice", Any], Any]

    #  Trigger when invoice creation starts.
    #  May return Invoice object.
    #  Overwrite to create invoice with proper data, call invoice.update_invoice.
    invoice_request: Callable[
        ["Order", "Invoice", Union[str, NoneType], Any], Optional["Invoice"]
    ]

    #  Trigger after invoice is sent.
    invoice_sent: Callable[["Invoice", str, Any], Any]

    list_payment_sources: Callable[[str, Any], List["CustomerSource"]]

    #  Trigger when menu is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a menu is
    #  created.
    menu_created: Callable[["Menu", None], None]

    #  Trigger when menu is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a menu is
    #  deleted.
    menu_deleted: Callable[["Menu", None], None]

    #  Trigger when menu is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a menu is
    #  updated.
    menu_updated: Callable[["Menu", None], None]

    #  Trigger when menu item is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a menu item is
    #  created.
    menu_item_created: Callable[["MenuItem", None], None]

    #  Trigger when menu item is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a menu item is
    #  deleted.
    menu_item_deleted: Callable[["MenuItem", None], None]

    #  Trigger when menu item is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a menu item is
    #  updated.
    menu_item_updated: Callable[["MenuItem", None], None]

    #  Handle notification request.
    #
    #  Overwrite this method if the plugin is responsible for sending notifications.
    notify: Callable[["NotifyEventType", dict, Any], Any]

    #  Trigger when order is cancelled.
    #
    #  Overwrite this method if you need to trigger specific logic when an order is
    #  canceled.
    order_cancelled: Callable[["Order", Any], Any]

    #  Trigger when order is confirmed by staff.
    #
    #  Overwrite this method if you need to trigger specific logic after an order is
    #  confirmed.
    order_confirmed: Callable[["Order", Any], Any]

    #  Trigger when order is created.
    #
    #  Overwrite this method if you need to trigger specific logic after an order is
    #  created.
    order_created: Callable[["Order", Any], Any]

    #  Trigger when order is fulfilled.
    #
    #  Overwrite this method if you need to trigger specific logic when an order is
    #  fulfilled.
    order_fulfilled: Callable[["Order", Any], Any]

    #  Trigger when order is fully paid.
    #
    #  Overwrite this method if you need to trigger specific logic when an order is
    #  fully paid.
    order_fully_paid: Callable[["Order", Any], Any]

    #  Trigger when order is updated.
    #
    #  Overwrite this method if you need to trigger specific logic when an order is
    #  changed.
    order_updated: Callable[["Order", Any], Any]

    #  Trigger when page is created.
    #
    #  Overwrite this method if you need to trigger specific logic when a page is
    #  created.
    page_created: Callable[["Page", Any], Any]

    #  Trigger when page is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic when a page is
    #  deleted.
    page_deleted: Callable[["Page", Any], Any]

    #  Trigger when page is updated.
    #
    #  Overwrite this method if you need to trigger specific logic when a page is
    #  updated.
    page_updated: Callable[["Page", Any], Any]

    #  Trigger directly before order creation.
    #
    #  Overwrite this method if you need to trigger specific logic before an order is
    #  created.
    preprocess_order_creation: Callable[
        [
            "CheckoutInfo",
            List["DiscountInfo"],
            Union[Iterable["CheckoutLineInfo"], NoneType],
            Any,
        ],
        Any,
    ]

    process_payment: Callable[["PaymentData", Any], Any]

    transaction_action_request: Callable[["TransactionActionData", None], None]

    #  Trigger when product is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a product is
    #  created.
    product_created: Callable[["Product", Any], Any]

    #  Trigger when product is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a product is
    #  deleted.
    product_deleted: Callable[["Product", List[int], Any], Any]

    #  Trigger when product is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a product is
    #  updated.
    product_updated: Callable[["Product", Any], Any]

    #  Trigger when product variant is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a product
    #  variant is created.
    product_variant_created: Callable[["ProductVariant", Any], Any]

    #  Trigger when product variant is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a product
    #  variant is deleted.
    product_variant_deleted: Callable[["ProductVariant", Any], Any]

    #  Trigger when product variant is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a product
    #  variant is updated.
    product_variant_updated: Callable[["ProductVariant", Any], Any]

    refund_payment: Callable[["PaymentData", Any], GatewayResponse]

    #  Trigger when sale is created.
    #
    # Overwrite this method if you need to trigger specific logic after sale is created.
    sale_created: Callable[["Sale", "NodeCatalogueInfo", Any], Any]

    #  Trigger when sale is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after sale is deleted.
    sale_deleted: Callable[["Sale", "NodeCatalogueInfo", Any], Any]

    #  Trigger when sale is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after sale is updated.
    sale_updated: Callable[["Sale", "NodeCatalogueInfo", "NodeCatalogueInfo", Any], Any]

    #  Trigger when shipping price is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a shipping
    #  price is created.
    shipping_price_created: Callable[["ShippingMethod", None], None]

    #  Trigger when shipping price is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a shipping
    #  price is deleted.
    shipping_price_deleted: Callable[["ShippingMethod", None], None]

    #  Trigger when shipping price is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a shipping
    #  price is updated.
    shipping_price_updated: Callable[["ShippingMethod", None], None]

    #  Trigger when shipping zone is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a shipping zone
    #  is created.
    shipping_zone_created: Callable[["ShippingZone", None], None]

    #  Trigger when shipping zone is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a shipping zone
    #  is deleted.
    shipping_zone_deleted: Callable[["ShippingZone", None], None]

    #  Trigger when shipping zone is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a shipping zone
    #  is updated.
    shipping_zone_updated: Callable[["ShippingZone", None], None]

    #  Define if storefront should add info about taxes to the price.
    #
    #  It is used only by the old storefront. The returned value determines if
    #  storefront should append info to the price about "including/excluding X% VAT".
    show_taxes_on_storefront: Callable[[bool], bool]

    #  Trigger when tracking number is updated.
    tracking_number_updated: Callable[["Fulfillment", Any], Any]

    void_payment: Callable[["PaymentData", Any], GatewayResponse]

    #  Trigger when voucher is created.
    #
    #  Overwrite this method if you need to trigger specific logic after a voucher is
    #  created.
    voucher_created: Callable[["Voucher", None], None]

    #  Trigger when voucher is deleted.
    #
    #  Overwrite this method if you need to trigger specific logic after a voucher is
    #  deleted.
    voucher_deleted: Callable[["Voucher", None], None]

    #  Trigger when voucher is updated.
    #
    #  Overwrite this method if you need to trigger specific logic after a voucher is
    #  updated.
    voucher_updated: Callable[["Voucher", None], None]

    #  Handle received http request.
    #
    #  Overwrite this method if the plugin expects the incoming requests.
    webhook: Callable[[WSGIRequest, str, Any], HttpResponse]

    # Triggers retry mechanism for event delivery
    event_delivery_retry: Callable[["EventDelivery", Any], EventDelivery]

    # Invoked before each mutation is executed
    #
    # This allows to trigger specific logic before the mutation is executed
    # but only once the permissions are checked.
    #
    # Returns one of:
    #     - null if the execution shall continue
    #     - an execution result
    #     - graphql.GraphQLError
    perform_mutation: Callable[
        [
            Optional[Union[ExecutionResult, GraphQLError]],  # previous value
            Mutation,  # mutation class
            Any,  # mutation root
            ResolveInfo,  # resolve info
            dict,  # mutation data
        ],
        Optional[Union[ExecutionResult, GraphQLError]],
    ]

    def token_is_required_as_payment_input(self, previous_value):
        return previous_value

    def get_payment_gateways(
        self, currency: Optional[str], checkout: Optional["Checkout"], previous_value
    ) -> List["PaymentGateway"]:
        payment_config = (
            self.get_payment_config(previous_value)  # type: ignore
            if hasattr(self, "get_payment_config")
            else []
        )
        currencies = (
            self.get_supported_currencies(previous_value=[])  # type: ignore
            if hasattr(self, "get_supported_currencies")
            else []
        )
        if currency and currency not in currencies:
            return []
        gateway = PaymentGateway(
            id=self.PLUGIN_ID,
            name=self.PLUGIN_NAME,
            config=payment_config,
            currencies=currencies,
        )
        return [gateway]

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
                    if item_type == ConfigurationTypeField.OUTPUT:
                        # OUTPUT field is read only. No need to update it
                        continue
                    config_item.update([("value", new_value)])

        # Get new keys that don't exist in current_config and extend it.
        current_config_keys = set(c_field["name"] for c_field in current_config)
        configuration_to_update_dict = {
            c_field["name"]: c_field["value"] for c_field in configuration_to_update
        }
        missing_keys = set(configuration_to_update_dict.keys()) - current_config_keys
        for missing_key in missing_keys:
            if not config_structure.get(missing_key):
                continue
            current_config.append(
                {
                    "name": missing_key,
                    "value": configuration_to_update_dict[missing_key],
                }
            )

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
        """Validate if provided configuration is correct.

        Raise django.core.exceptions.ValidationError otherwise.
        """
        return

    @classmethod
    def pre_save_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Trigger before plugin configuration will be saved.

        Overwrite this method if you need to trigger specific logic before saving a
        plugin configuration.
        """

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
        cls.pre_save_plugin_configuration(plugin_configuration)
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
        fields_without_structure = []
        for configuration_field in configuration:

            structure_to_add = config_structure.get(configuration_field.get("name"))
            if structure_to_add:
                configuration_field.update(structure_to_add)
            else:
                fields_without_structure.append(configuration_field)

        if fields_without_structure:
            [
                configuration.remove(field)  # type: ignore
                for field in fields_without_structure
            ]

    @classmethod
    def _update_configuration_structure(cls, configuration: PluginConfigurationType):
        updated_configuration = []
        config_structure = getattr(cls, "CONFIG_STRUCTURE") or {}
        desired_config_keys = set(config_structure.keys())
        for config_field in configuration:
            if config_field["name"] not in desired_config_keys:
                continue
            updated_configuration.append(copy(config_field))

        configured_keys = set(d["name"] for d in updated_configuration)
        missing_keys = desired_config_keys - configured_keys

        if not missing_keys:
            return updated_configuration

        default_config = cls.DEFAULT_CONFIGURATION
        if not default_config:
            return updated_configuration

        update_values = [copy(k) for k in default_config if k["name"] in missing_keys]
        if update_values:
            updated_configuration.extend(update_values)
        return updated_configuration

    @classmethod
    def get_default_active(cls):
        return cls.DEFAULT_ACTIVE

    def get_plugin_configuration(
        self, configuration: PluginConfigurationType
    ) -> PluginConfigurationType:
        if not configuration:
            configuration = []
        configuration = self._update_configuration_structure(configuration)
        if configuration:
            # Let's add a translated descriptions and labels
            self._append_config_structure(configuration)
        return configuration

    def resolve_plugin_configuration(
        self, request
    ) -> Union[PluginConfigurationType, Promise[PluginConfigurationType]]:
        # Override this function to customize resolving plugin configuration in API.
        return self.configuration

    def is_event_active(self, event: str, channel=Optional[str]):
        return hasattr(self, event)
