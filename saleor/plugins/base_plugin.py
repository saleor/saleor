from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.utils.functional import SimpleLazyObject
from prices import TaxedMoney
from promise.promise import Promise

from ..core.models import EventDelivery
from ..payment.interface import (
    CustomerSource,
    GatewayResponse,
    InitializedPaymentResponse,
    ListStoredPaymentMethodsRequestData,
    PaymentData,
    PaymentGateway,
    PaymentGatewayInitializeTokenizationRequestData,
    PaymentGatewayInitializeTokenizationResponseData,
    PaymentMethodData,
    PaymentMethodInitializeTokenizationRequestData,
    PaymentMethodProcessTokenizationRequestData,
    PaymentMethodTokenizationResponseData,
    StoredPaymentMethodRequestDeleteData,
    StoredPaymentMethodRequestDeleteResponseData,
    TransactionActionData,
    TransactionSessionResult,
)
from ..thumbnail.models import Thumbnail
from .models import PluginConfiguration

if TYPE_CHECKING:
    from ..account.models import Address, Group, User
    from ..app.models import App
    from ..attribute.models import Attribute, AttributeValue
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..checkout.models import Checkout
    from ..core.middleware import Requestor
    from ..core.notify import NotifyEventType
    from ..core.taxes import TaxData, TaxType
    from ..csv.models import ExportFile
    from ..discount.models import Promotion, PromotionRule, Voucher, VoucherCode
    from ..giftcard.models import GiftCard
    from ..invoice.models import Invoice
    from ..menu.models import Menu, MenuItem
    from ..order.models import Fulfillment, Order, OrderLine
    from ..page.models import Page, PageType
    from ..payment.interface import PaymentGatewayData, TransactionSessionData
    from ..payment.models import TransactionItem
    from ..product.models import (
        Category,
        Collection,
        Product,
        ProductMedia,
        ProductType,
        ProductVariant,
    )
    from ..shipping.interface import ShippingMethodData
    from ..shipping.models import ShippingMethod, ShippingZone
    from ..site.models import SiteSettings
    from ..tax.models import TaxClass
    from ..warehouse.models import Stock, Warehouse

PluginConfigurationType = list[dict]
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
        db_config: Optional["PluginConfiguration"] = None,
        allow_replica: bool = True,
    ):
        self.configuration = self.get_plugin_configuration(configuration)
        self.active = active
        self.channel = channel
        self.requestor: Optional[RequestorOrLazyObject] = (
            SimpleLazyObject(requestor_getter) if requestor_getter else requestor_getter
        )
        self.db_config = db_config
        self.allow_replica = allow_replica

    def __del__(self) -> None:
        self.channel = None
        self.db_config = None
        self.configuration.clear()
        self.requestor = None

    def __str__(self):
        return self.PLUGIN_NAME

    # Trigger when account is confirmed by user.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # is confirmed.
    #
    # Note: this method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from plugin to core modules.
    account_confirmed: Callable[["User", None], None]

    # Trigger when account confirmation is requested.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # confirmation is requested.
    #
    # Note: this method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from plugin to core modules.
    account_confirmation_requested: Callable[
        ["User", str, str, Optional[str], None], None
    ]

    # Trigger when account change email is requested.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # change email is requested.
    #
    # Note: this method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from plugin to core modules.
    account_change_email_requested: Callable[["User", str, str, str, str, None], None]

    # Trigger when account set password is requested.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # set password is requested.
    #
    # Note: this method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from plugin to core modules.
    account_set_password_requested: Callable[["User", str, str, str, None], None]

    # Trigger when account delete is confirmed.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # delete is confirmed.
    #
    # Note: this method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from plugin to core modules.
    account_deleted: Callable[["User", None], None]

    # Trigger when account email is changed.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # email is changed.
    #
    # Note: this method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from plugin to core modules.
    account_email_changed: Callable[["User", None], None]

    # Trigger when account delete is requested.
    #
    # Overwrite this method if you need to trigger specific logic after an account
    # delete is requested.
    #
    # Note: this method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from plugin to core modules.
    account_delete_requested: Callable[["User", str, str, str, None], None]

    # Triggered when an address is created.
    #
    # Overwrite this method if you need to trigger specific logic after an address is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    address_created: Callable[["Address", None], None]

    # Triggered when an address is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after an address is
    # deleted.
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    address_deleted: Callable[["Address", None], None]

    # Triggered when an address is updated.
    #
    # Overwrite this method if you need to trigger specific logic after an address is
    # updated.
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    address_updated: Callable[["Address", None], None]

    # Trigger when app is installed.
    #
    # Overwrite this method if you need to trigger specific logic after an app is
    # installed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    app_installed: Callable[["App", None], None]

    # Trigger when app is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after an app is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    app_deleted: Callable[["App", None], None]

    # Trigger when app is updated.
    #
    # Overwrite this method if you need to trigger specific logic after an app is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    app_updated: Callable[["App", None], None]

    # Trigger when channel status is changed.
    #
    # Overwrite this method if you need to trigger specific logic after an app
    # status is changed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    app_status_changed: Callable[["App", None], None]

    # Trigger when attribute is created.
    #
    # Overwrite this method if you need to trigger specific logic after an attribute is
    # installed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    attribute_created: Callable[["Attribute", None, None], None]

    # Trigger when attribute is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after an attribute is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    attribute_deleted: Callable[["Attribute", None, None], None]

    # Trigger when attribute is updated.
    #
    # Overwrite this method if you need to trigger specific logic after an attribute is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    attribute_updated: Callable[["Attribute", None, None], None]

    # Trigger when attribute value is created.
    #
    # Overwrite this method if you need to trigger specific logic after an attribute
    # value is installed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    attribute_value_created: Callable[["AttributeValue", None], None]

    # Trigger when attribute value is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after an attribute
    # value is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    attribute_value_deleted: Callable[["AttributeValue", None, None], None]

    # Trigger when attribute value is updated.
    #
    # Overwrite this method if you need to trigger specific logic after an attribute
    # value is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    attribute_value_updated: Callable[["AttributeValue", None], None]

    # Authenticate user which should be assigned to the request.
    #
    # Overwrite this method if the plugin handles authentication flow.
    authenticate_user: Callable[[WSGIRequest, Optional["User"]], Union["User", None]]

    authorize_payment: Callable[["PaymentData", Any], GatewayResponse]

    # Calculate checkout line total.
    #
    # Overwrite this method if you need to apply specific logic for the calculation
    # of a checkout line total. Return TaxedMoney.
    calculate_checkout_line_total: Callable[
        [
            "CheckoutInfo",
            list["CheckoutLineInfo"],
            "CheckoutLineInfo",
            Union["Address", None],
            TaxedMoney,
        ],
        TaxedMoney,
    ]

    # Calculate checkout line unit price.
    calculate_checkout_line_unit_price: Callable[
        [
            "CheckoutInfo",
            list["CheckoutLineInfo"],
            "CheckoutLineInfo",
            Union["Address", None],
            Any,
        ],
        TaxedMoney,
    ]

    # Calculate the shipping costs for checkout.
    #
    # Overwrite this method if you need to apply specific logic for the calculation
    # of shipping costs. Return TaxedMoney.
    calculate_checkout_shipping: Callable[
        [
            "CheckoutInfo",
            list["CheckoutLineInfo"],
            Union["Address", None],
            TaxedMoney,
        ],
        TaxedMoney,
    ]

    # Calculate the total for checkout.
    #
    # Overwrite this method if you need to apply specific logic for the calculation
    # of a checkout total. Return TaxedMoney.
    calculate_checkout_total: Callable[
        [
            "CheckoutInfo",
            list["CheckoutLineInfo"],
            Union["Address", None],
            TaxedMoney,
        ],
        TaxedMoney,
    ]

    # Calculate the subtotal for checkout.
    #
    # Overwrite this method if you need to apply specific logic for the calculation
    # of a checkout subtotal. Return TaxedMoney.
    calculate_checkout_subtotal: Callable[
        [
            "CheckoutInfo",
            list["CheckoutLineInfo"],
            Union["Address", None],
            TaxedMoney,
        ],
        TaxedMoney,
    ]

    # Calculate order line total.
    #
    # Overwrite this method if you need to apply specific logic for the calculation
    # of a order line total. Return TaxedMoney.
    calculate_order_line_total: Callable[
        ["Order", "OrderLine", "ProductVariant", "Product", TaxedMoney], TaxedMoney
    ]

    # Calculate order line unit price.
    #
    # Update order line unit price in the order in case of changes in draft order.
    # Return TaxedMoney.
    # Overwrite this method if you need to apply specific logic for the calculation
    # of an order line unit price.
    calculate_order_line_unit: Callable[
        ["Order", "OrderLine", "ProductVariant", "Product", TaxedMoney], TaxedMoney
    ]

    # Calculate the shipping costs for the order.
    #
    # Update shipping costs in the order in case of changes in shipping address or
    # changes in draft order. Return TaxedMoney.
    calculate_order_shipping: Callable[["Order", TaxedMoney], TaxedMoney]

    # Calculate order total.
    #
    # Overwrite this method if you need to apply specific logic for the calculation
    # of a order total. Return TaxedMoney.
    calculate_order_total: Callable[
        ["Order", list["OrderLine"], TaxedMoney], TaxedMoney
    ]

    capture_payment: Callable[["PaymentData", Any], GatewayResponse]

    # Trigger when category is created.
    #
    # Overwrite this method if you need to trigger specific logic after a category is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    category_created: Callable[["Category", None], None]

    # Trigger when category is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a category is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    category_deleted: Callable[["Category", None, None], None]

    # Trigger when category is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a category is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    category_updated: Callable[["Category", None], None]

    # Trigger when channel is created.
    #
    # Overwrite this method if you need to trigger specific logic after a channel is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    channel_created: Callable[["Channel", None], None]

    # Trigger when channel is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a channel is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    channel_deleted: Callable[["Channel", None], None]

    # Trigger when channel is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a channel is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    channel_updated: Callable[["Channel", None, None], None]

    # Trigger when channel status is changed.
    #
    # Overwrite this method if you need to trigger specific logic after a channel
    # status is changed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    channel_status_changed: Callable[["Channel", None], None]

    # Trigger when channel metadata is changed.
    #
    # Overwrite this method if you need to trigger specific logic after a channel
    # metadata is changed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    channel_metadata_updated: Callable[["Channel", None], None]

    change_user_address: Callable[
        ["Address", Union[str, None], Union["User", None], bool, "Address"], "Address"
    ]

    # Retrieves the balance remaining on a shopper's gift card
    check_payment_balance: Callable[[dict, str], dict]

    # Trigger when checkout is created.
    #
    # Overwrite this method if you need to trigger specific logic when a checkout is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    checkout_created: Callable[["Checkout", Any, None], Any]

    # Trigger when checkout is updated.
    #
    # Overwrite this method if you need to trigger specific logic when a checkout is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    checkout_updated: Callable[["Checkout", Any, None], Any]

    # Trigger when checkout is fully paid with transactions.
    #
    # Overwrite this method if you need to trigger specific logic when a checkout is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    checkout_fully_paid: Callable[["Checkout", Any, None], Any]

    # Trigger when checkout metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic when a checkout
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    checkout_metadata_updated: Callable[["Checkout", Any, None], Any]

    # Trigger when collection is created.
    #
    # Overwrite this method if you need to trigger specific logic after a collection is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    collection_created: Callable[["Collection", Any], Any]

    # Trigger when collection is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a collection is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    collection_deleted: Callable[["Collection", Any, None], Any]

    # Trigger when collection is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a collection is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    collection_updated: Callable[["Collection", Any], Any]

    # Trigger when collection metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a collection
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    collection_metadata_updated: Callable[["Collection", Any], Any]

    confirm_payment: Callable[["PaymentData", Any], GatewayResponse]

    # Trigger when user is created.
    #
    # Overwrite this method if you need to trigger specific logic after a user is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    customer_created: Callable[["User", Any], Any]

    # Trigger when user is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a user is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    customer_deleted: Callable[["User", Any, None], Any]

    # Trigger when user is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a user is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    customer_updated: Callable[["User", Any, None], Any]

    # Trigger when user metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a user
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    customer_metadata_updated: Callable[["User", Any, None], Any]

    # Handle authentication request.
    #
    # Overwrite this method if the plugin handles authentication flow.
    external_authentication_url: Callable[[dict, WSGIRequest, dict], dict]

    # Handle logout request.
    #
    # Overwrite this method if the plugin handles logout flow.
    external_logout: Callable[[dict, WSGIRequest, dict], Any]

    # Handle authentication request responsible for obtaining access tokens.
    #
    # Overwrite this method if the plugin handles authentication flow.
    external_obtain_access_tokens: Callable[
        [dict, WSGIRequest, ExternalAccessTokens], ExternalAccessTokens
    ]

    # Handle authentication refresh request.
    #
    # Overwrite this method if the plugin handles authentication flow and supports
    # refreshing the access.
    external_refresh: Callable[
        [dict, WSGIRequest, ExternalAccessTokens], ExternalAccessTokens
    ]

    # Verify the provided authentication data.
    #
    # Overwrite this method if the plugin should validate the authentication data.
    external_verify: Callable[
        [dict, WSGIRequest, tuple[Union["User", None], dict]],
        tuple[Union["User", None], dict],
    ]

    # Trigger when fulfillment is created.
    #
    # Overwrite this method if you need to trigger specific logic when a fulfillment is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    fulfillment_created: Callable[["Fulfillment", bool, Any], Any]

    # Trigger when fulfillment is cancelled.
    #
    # Overwrite this method if you need to trigger specific logic when a fulfillment is
    # cancelled.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    fulfillment_canceled: Callable[["Fulfillment", Any], Any]

    # Trigger when fulfillment is approved.
    #
    # Overwrite this method if you need to trigger specific logic when a fulfillment is
    # approved.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    fulfillment_approved: Callable[["Fulfillment", Any], Any]

    # Trigger when fulfillment metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic when a fulfillment
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    fulfillment_metadata_updated: Callable[["Fulfillment", Any], Any]

    get_checkout_line_tax_rate: Callable[
        [
            "CheckoutInfo",
            list["CheckoutLineInfo"],
            "CheckoutLineInfo",
            Union["Address", None],
            Decimal,
        ],
        Decimal,
    ]

    get_checkout_shipping_tax_rate: Callable[
        [
            "CheckoutInfo",
            list["CheckoutLineInfo"],
            Union["Address", None],
            Any,
        ],
        Any,
    ]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    get_taxes_for_checkout: Callable[
        ["CheckoutInfo", list["CheckoutLineInfo"], str, Any, Optional[dict]],
        Optional["TaxData"],
    ]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    get_taxes_for_order: Callable[["Order", str, Any], Optional["TaxData"]]

    get_client_token: Callable[[Any, Any], Any]

    get_order_line_tax_rate: Callable[
        ["Order", "Product", "ProductVariant", Union["Address", None], Decimal],
        Decimal,
    ]

    get_order_shipping_tax_rate: Callable[["Order", Any], Any]
    get_payment_config: Callable[[Any], Any]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    get_shipping_methods_for_checkout: Callable[
        ["Checkout", Any], list["ShippingMethodData"]
    ]

    get_supported_currencies: Callable[[Any], Any]

    # Return tax code from object meta.
    get_tax_code_from_object_meta: Callable[
        [
            Union["Product", "ProductType", "TaxClass"],
            "TaxType",
        ],
        "TaxType",
    ]

    # Return list of all tax categories.
    #
    # The returned list will be used to provide staff users with the possibility to
    # assign tax categories to a product. It can be used by tax plugins to properly
    # calculate taxes for products.
    # Overwrite this method in case your plugin provides a list of tax categories.
    get_tax_rate_type_choices: Callable[[list["TaxType"]], list["TaxType"]]

    # Trigger when gift card is created.
    #
    # Overwrite this method if you need to trigger specific logic after a gift card is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    gift_card_created: Callable[["GiftCard", None, None], None]

    # Trigger when gift card is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a gift card is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    gift_card_deleted: Callable[["GiftCard", None, None], None]

    # Trigger when gift card is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a gift card is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    gift_card_updated: Callable[["GiftCard", None], None]

    # Trigger when gift card metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a gift card
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    gift_card_metadata_updated: Callable[["GiftCard", None], None]

    # Trigger when gift card status is changed.
    #
    # Overwrite this method if you need to trigger specific logic after a gift card
    # status is changed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    gift_card_status_changed: Callable[["GiftCard", None, None], None]

    # Trigger when gift cards export is completed.
    #
    # Overwrite this method if you need to trigger specific logic after a gift cards
    # export is completed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    gift_card_export_completed: Callable[["ExportFile", None], None]

    # Trigger when draft order is created.
    #
    # Overwrite this method if you need to trigger specific logic after an order is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    draft_order_created: Callable[["Order", Any, None], Any]

    # Trigger when draft order is updated.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # changed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    draft_order_updated: Callable[["Order", Any, None], Any]

    # Trigger when draft order is deleted.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # changed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    draft_order_deleted: Callable[["Order", Any, None], Any]

    initialize_payment: Callable[
        [dict, Optional[InitializedPaymentResponse]], InitializedPaymentResponse
    ]

    # Trigger before invoice is deleted.
    #
    # Perform any extra logic before the invoice gets deleted.
    # Note there is no need to run invoice.delete() as it will happen in mutation.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    invoice_delete: Callable[["Invoice", Any], Any]

    # Trigger when invoice creation starts.
    # May return Invoice object.
    # Overwrite to create invoice with proper data, call invoice.update_invoice.
    invoice_request: Callable[
        ["Order", "Invoice", Union[str, None], Any], Optional["Invoice"]
    ]

    # Trigger after invoice is sent.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    invoice_sent: Callable[["Invoice", str, Any], Any]

    list_payment_sources: Callable[[str, Any], list["CustomerSource"]]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    list_stored_payment_methods: Callable[
        ["ListStoredPaymentMethodsRequestData", list["PaymentMethodData"]],
        list["PaymentMethodData"],
    ]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    stored_payment_method_request_delete: Callable[
        [
            "StoredPaymentMethodRequestDeleteData",
            "StoredPaymentMethodRequestDeleteResponseData",
        ],
        "StoredPaymentMethodRequestDeleteResponseData",
    ]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    payment_gateway_initialize_tokenization: Callable[
        [
            "PaymentGatewayInitializeTokenizationRequestData",
            "PaymentGatewayInitializeTokenizationResponseData",
        ],
        "PaymentGatewayInitializeTokenizationResponseData",
    ]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    payment_method_initialize_tokenization: Callable[
        [
            "PaymentMethodInitializeTokenizationRequestData",
            "PaymentMethodTokenizationResponseData",
        ],
        "PaymentMethodTokenizationResponseData",
    ]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    payment_method_process_tokenization: Callable[
        [
            "PaymentMethodProcessTokenizationRequestData",
            "PaymentMethodTokenizationResponseData",
        ],
        "PaymentMethodTokenizationResponseData",
    ]

    # Trigger when menu is created.
    #
    # Overwrite this method if you need to trigger specific logic after a menu is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    menu_created: Callable[["Menu", None], None]

    # Trigger when menu is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a menu is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    menu_deleted: Callable[["Menu", None, None], None]

    # Trigger when menu is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a menu is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    menu_updated: Callable[["Menu", None], None]

    # Trigger when menu item is created.
    #
    # Overwrite this method if you need to trigger specific logic after a menu item is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    menu_item_created: Callable[["MenuItem", None], None]

    # Trigger when menu item is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a menu item is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    menu_item_deleted: Callable[["MenuItem", None, None], None]

    # Trigger when menu item is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a menu item is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    menu_item_updated: Callable[["MenuItem", None], None]

    # Handle notification request.
    #
    # Overwrite this method if the plugin is responsible for sending notifications.
    notify: Callable[["NotifyEventType", Callable[[], dict], Any], Any]

    # Trigger when order is cancelled.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # canceled.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_cancelled: Callable[["Order", Any, None], Any]

    # Trigger when order is expired.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # expired.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_expired: Callable[["Order", Any, None], Any]

    # Trigger when order is confirmed by staff.
    #
    # Overwrite this method if you need to trigger specific logic after an order is
    # confirmed.
    order_confirmed: Callable[["Order", Any, None], Any]

    # Trigger when order is created.
    #
    # Overwrite this method if you need to trigger specific logic after an order is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_created: Callable[["Order", Any, None], Any]

    # Trigger when order is fulfilled.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # fulfilled.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_fulfilled: Callable[["Order", Any, None], Any]

    # Trigger when order is fully paid.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # fully paid.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_fully_paid: Callable[["Order", Any, None], Any]

    # Trigger when order is paid.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # received the payment.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_paid: Callable[["Order", Any, None], Any]

    # Trigger when order is refunded.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # refunded.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_refunded: Callable[["Order", Any, None], Any]

    # Trigger when order is fully refunded.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # fully refunded.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_fully_refunded: Callable[["Order", Any, None], Any]

    # Trigger when order is updated.
    #
    # Overwrite this method if you need to trigger specific logic when an order is
    # changed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_updated: Callable[["Order", Any, None], Any]

    # Trigger when order metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic when an order
    # metadata is changed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_metadata_updated: Callable[["Order", Any, None], Any]

    # Trigger when orders are imported.
    #
    # Overwrite this method if you need to trigger specific logic when an order
    # is imported.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    order_bulk_created: Callable[[list["Order"], Any], Any]

    # Trigger when page is created.
    #
    # Overwrite this method if you need to trigger specific logic when a page is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    page_created: Callable[["Page", Any], Any]

    # Trigger when page is deleted.
    #
    # Overwrite this method if you need to trigger specific logic when a page is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    page_deleted: Callable[["Page", Any], Any]

    # Trigger when page is updated.
    #
    # Overwrite this method if you need to trigger specific logic when a page is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    page_updated: Callable[["Page", Any], Any]

    # Trigger when page type is created.
    #
    # Overwrite this method if you need to trigger specific logic when a page type is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    page_type_created: Callable[["PageType", Any], Any]

    # Trigger when page type is deleted.
    #
    # Overwrite this method if you need to trigger specific logic when a page type is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    page_type_deleted: Callable[["PageType", Any, None], Any]

    # Trigger when page type is updated.
    #
    # Overwrite this method if you need to trigger specific logic when a page type is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    page_type_updated: Callable[["PageType", Any], Any]

    # Trigger when permission group is created.
    #
    # Overwrite this method if you need to trigger specific logic when a permission
    # group is created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    permission_group_created: Callable[["Group", Any], Any]

    # Trigger when permission group type is deleted.
    #
    # Overwrite this method if you need to trigger specific logic when a permission
    # group is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    permission_group_deleted: Callable[["Group", Any], Any]

    # Trigger when permission group is updated.
    #
    # Overwrite this method if you need to trigger specific logic when a permission
    # group is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    permission_group_updated: Callable[["Group", Any], Any]

    # Trigger directly before order creation.
    #
    # Overwrite this method if you need to trigger specific logic before an order is
    # created.
    preprocess_order_creation: Callable[
        [
            "CheckoutInfo",
            Union[list["CheckoutLineInfo"], None],
            Any,
        ],
        Any,
    ]

    process_payment: Callable[["PaymentData", Any], Any]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    transaction_charge_requested: Callable[["TransactionActionData", None], None]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    transaction_cancelation_requested: Callable[["TransactionActionData", None], None]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    transaction_refund_requested: Callable[["TransactionActionData", None], None]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    payment_gateway_initialize_session: Callable[
        [
            Decimal,
            Optional[list["PaymentGatewayData"]],
            Union["Checkout", "Order"],
            None,
        ],
        list["PaymentGatewayData"],
    ]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    transaction_initialize_session: Callable[
        ["TransactionSessionData", None], "TransactionSessionResult"
    ]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    transaction_process_session: Callable[
        ["TransactionSessionData", None], "TransactionSessionResult"
    ]

    # Trigger when transaction item metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic when a transaction
    # item metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    transaction_item_metadata_updated: Callable[["TransactionItem", Any], Any]

    # Trigger when product is created.
    #
    # Overwrite this method if you need to trigger specific logic after a product is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_created: Callable[["Product", Any, None], Any]

    # Trigger when product is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a product is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_deleted: Callable[["Product", list[int], Any, None], Any]

    # Trigger when product is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a product is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_updated: Callable[["Product", Any, None], Any]

    # Trigger when product media is created.
    #
    # Overwrite this method if you need to trigger specific logic after a product media
    # is created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_media_created: Callable[["ProductMedia", Any], Any]

    # Trigger when product media is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a product media
    # is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_media_updated: Callable[["ProductMedia", Any], Any]

    # Trigger when product media is created.
    #
    # Overwrite this method if you need to trigger specific logic after a product media
    # is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_media_deleted: Callable[["ProductMedia", Any], Any]

    # Trigger when product metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_metadata_updated: Callable[["Product", Any], Any]

    # Trigger when product variant is created.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # variant is created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_variant_created: Callable[["ProductVariant", Any, None], Any]

    # Trigger when product variant is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # variant is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_variant_deleted: Callable[["ProductVariant", Any, None], Any]

    # Trigger when product variant is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # variant is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_variant_updated: Callable[["ProductVariant", Any, None], Any]

    # Trigger when product variant metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # variant metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_variant_metadata_updated: Callable[["ProductVariant", Any], Any]

    # Trigger when product variant is out of stock.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # variant is out of stock.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_variant_out_of_stock: Callable[["Stock", None, None], Any]

    # Trigger when product variant is back in stock.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # variant is back in stock.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_variant_back_in_stock: Callable[["Stock", None, None], Any]

    # Trigger when product variant stock is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # variant stock is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_variant_stocks_updated: Callable[[list["Stock"], None, None], Any]

    # Trigger when a product export is completed.
    #
    # Overwrite this method if you need to trigger specific logic after a product
    # export is completed.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    product_export_completed: Callable[["ExportFile", None], None]

    refund_payment: Callable[["PaymentData", Any], GatewayResponse]

    # Trigger when sale is created.
    #
    # Overwrite this method if you need to trigger specific logic after sale is created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    sale_created: Callable[["Promotion", defaultdict[str, set[str]], Any], Any]

    # Trigger when sale is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a sale is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    sale_deleted: Callable[["Promotion", defaultdict[str, set[str]], Any], Any]

    # Trigger when sale is updated.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a sale is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    sale_updated: Callable[
        ["Promotion", defaultdict[str, set[str]], defaultdict[str, set[str]], Any], Any
    ]

    # Trigger when promotion is created.
    #
    # Overwrite this method if you need to trigger specific logic after promotion
    # is created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    promotion_created: Callable[["Promotion", Any], Any]

    # Trigger when promotion is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a promotion is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    promotion_deleted: Callable[["Promotion", Any, None], Any]

    # Trigger when promotion is updated.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a promotion is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    promotion_updated: Callable[["Promotion", Any], Any]

    # Trigger when promotion is started.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a promotion is started.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    promotion_started: Callable[["Promotion", Any], Any]

    # Trigger when promotion is ended.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a promotion is ended.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    promotion_ended: Callable[["Promotion", Any], Any]

    # Trigger when promotion rule is created.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a promotion rule is created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    promotion_rule_created: Callable[["PromotionRule", Any], Any]

    # Trigger when promotion rule is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a promotion rule is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    promotion_rule_deleted: Callable[["PromotionRule", Any], Any]

    # Trigger when promotion rule is updated.
    #
    # Overwrite this method if you need to trigger specific logic after
    # a promotion rule is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    promotion_rule_updated: Callable[["PromotionRule", Any], Any]

    # Trigger when shipping price is created.
    #
    # Overwrite this method if you need to trigger specific logic after a shipping
    # price is created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    shipping_price_created: Callable[["ShippingMethod", None], None]

    # Trigger when shipping price is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a shipping
    # price is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    shipping_price_deleted: Callable[["ShippingMethod", None, None], None]

    # Trigger when shipping price is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a shipping
    # price is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    shipping_price_updated: Callable[["ShippingMethod", None], None]

    # Trigger when shipping zone is created.
    #
    # Overwrite this method if you need to trigger specific logic after a shipping zone
    # is created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    shipping_zone_created: Callable[["ShippingZone", None], None]

    # Trigger when shipping zone is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a shipping zone
    # is deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    shipping_zone_deleted: Callable[["ShippingZone", None, None], None]

    # Trigger when shipping zone is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a shipping zone
    # is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    shipping_zone_updated: Callable[["ShippingZone", None], None]

    # Trigger when shipping zone metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a shipping zone
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    shipping_zone_metadata_updated: Callable[["ShippingZone", None], None]

    # Trigger when staff user is created.
    #
    # Overwrite this method if you need to trigger specific logic after a staff user is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    staff_created: Callable[["User", Any], Any]

    # Trigger when staff user is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a staff user is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    staff_updated: Callable[["User", Any], Any]

    # Trigger when staff user is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a staff user is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    staff_deleted: Callable[["User", Any, None], Any]

    # Trigger when setting a password for staff is requested.
    #
    # Overwrite this method if you need to trigger specific logic after set
    # password for staff is requested.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    staff_set_password_requested: Callable[["User", str, str, str, None], None]

    # Trigger when thumbnail is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    thumbnail_created: Callable[["Thumbnail", Any], Any]

    # Trigger when tracking number is updated.
    tracking_number_updated: Callable[["Fulfillment", Any], Any]

    void_payment: Callable[["PaymentData", Any], GatewayResponse]

    # Trigger when warehouse is created.
    #
    # Overwrite this method if you need to trigger specific logic after a warehouse is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    warehouse_created: Callable[["Warehouse", None], None]

    # Trigger when warehouse is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a warehouse is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    warehouse_deleted: Callable[["Warehouse", None], None]

    # Trigger when warehouse is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a warehouse is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    warehouse_updated: Callable[["Warehouse", None], None]

    # Trigger when warehouse metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a warehouse
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    warehouse_metadata_updated: Callable[["Warehouse", None], None]

    # Trigger when voucher is created.
    #
    # Overwrite this method if you need to trigger specific logic after a voucher is
    # created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    voucher_created: Callable[["Voucher", str, None], None]

    # Trigger when voucher is deleted.
    #
    # Overwrite this method if you need to trigger specific logic after a voucher is
    # deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    voucher_deleted: Callable[["Voucher", str, None, None], None]

    # Trigger when voucher is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a voucher is
    # updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    voucher_updated: Callable[["Voucher", str, None], None]

    # Trigger when voucher codes are created.
    #
    # Overwrite this method if you need to trigger specific logic after voucher codes
    # are created.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    voucher_codes_created: Callable[[list["VoucherCode"], None, None], None]

    # Trigger when voucher code are deleted.
    #
    # Overwrite this method if you need to trigger specific logic after voucher codes
    # are deleted.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    voucher_codes_deleted: Callable[[list["VoucherCode"], None, None], None]

    # Trigger when voucher metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a voucher
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    voucher_metadata_updated: Callable[["Voucher", None], None]

    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    voucher_code_export_completed: Callable[["ExportFile", None], None]

    # Trigger when shop metadata is updated.
    #
    # Overwrite this method if you need to trigger specific logic after a shop
    # metadata is updated.
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    shop_metadata_updated: Callable[["SiteSettings", None], None]

    # Handle received http request.
    #
    # Overwrite this method if the plugin expects the incoming requests.
    webhook: Callable[[WSGIRequest, str, Any], HttpResponse]

    # Triggers retry mechanism for event delivery
    #
    # Note: This method is deprecated in Saleor 3.20 and will be removed in Saleor 3.21.
    # Webhook-related functionality will be moved from the plugin to core modules.
    event_delivery_retry: Callable[[EventDelivery, None], None]

    def token_is_required_as_payment_input(self, previous_value):
        return previous_value

    def get_payment_gateways(
        self,
        currency: Optional[str],
        checkout_info: Optional["CheckoutInfo"],
        checkout_lines: Optional[list["CheckoutLineInfo"]],
        previous_value,
    ) -> list["PaymentGateway"]:
        payment_config = (
            self.get_payment_config(previous_value)
            if hasattr(self, "get_payment_config")
            else []
        )
        currencies = (
            self.get_supported_currencies([])
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
        cls, configuration_to_update: list[dict], current_config: list[dict]
    ):
        config_structure: dict = (
            cls.CONFIG_STRUCTURE if cls.CONFIG_STRUCTURE is not None else {}
        )
        configuration_to_update_dict = {
            c_field["name"]: c_field.get("value") for c_field in configuration_to_update
        }
        for config_item in current_config:
            new_value = configuration_to_update_dict.get(config_item["name"])
            if new_value is None:
                continue
            item_type = config_structure.get(config_item["name"], {}).get("type")
            new_value = cls._clean_configuration_value(item_type, new_value)
            if new_value is not None:
                config_item.update([("value", new_value)])

        # Get new keys that don't exist in current_config and extend it.
        current_config_keys = {c_field["name"] for c_field in current_config}
        missing_keys = set(configuration_to_update_dict.keys()) - current_config_keys
        for missing_key in missing_keys:
            if not config_structure.get(missing_key):
                continue
            item_type = config_structure.get(missing_key, {}).get("type")
            new_value = cls._clean_configuration_value(
                item_type, configuration_to_update_dict[missing_key]
            )
            if new_value is None:
                continue
            current_config.append(
                {
                    "name": missing_key,
                    "value": new_value,
                }
            )

    @classmethod
    def _clean_configuration_value(cls, item_type, new_value):
        """Clean the value that is saved in plugin configuration.

        Change the string provided as boolean into the bool value.
        Return None for Output type, as it's read only field.
        """
        if (
            item_type == ConfigurationTypeField.BOOLEAN
            and new_value
            and not isinstance(new_value, bool)
        ):
            new_value = new_value.lower() == "true"
        if item_type == ConfigurationTypeField.OUTPUT:
            # OUTPUT field is read only. No need to update it
            return None
        return new_value

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

        for field in fields_without_structure:
            configuration.remove(field)

    @classmethod
    def _update_configuration_structure(cls, configuration: PluginConfigurationType):
        updated_configuration = []
        config_structure = getattr(cls, "CONFIG_STRUCTURE") or {}
        desired_config_keys = set(config_structure.keys())
        for config_field in configuration:
            if config_field["name"] not in desired_config_keys:
                continue
            updated_configuration.append(copy(config_field))

        configured_keys = {d["name"] for d in updated_configuration}
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
