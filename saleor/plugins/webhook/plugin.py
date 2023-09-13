import json
import logging
from decimal import Decimal
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Final,
    Iterable,
    List,
    Optional,
    Set,
    Union,
)

import graphene

from ...app.models import App
from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ...checkout.models import Checkout
from ...core import EventDeliveryStatus
from ...core.models import EventDelivery
from ...core.notify_events import NotifyEventType
from ...core.taxes import TaxData, TaxType
from ...core.utils import build_absolute_uri
from ...core.utils.json_serializer import CustomJsonEncoder
from ...csv.notifications import get_default_export_payload
from ...graphql.core.context import SaleorContext
from ...graphql.webhook.subscription_payload import initialize_request
from ...payment import PaymentError, TransactionKind
from ...payment.interface import (
    GatewayResponse,
    ListStoredPaymentMethodsRequestData,
    PaymentData,
    PaymentGateway,
    PaymentGatewayData,
    PaymentGatewayInitializeTokenizationRequestData,
    PaymentGatewayInitializeTokenizationResponseData,
    PaymentMethodData,
    PaymentMethodInitializeTokenizationRequestData,
    PaymentMethodProcessTokenizationRequestData,
    PaymentMethodTokenizationBaseRequestData,
    PaymentMethodTokenizationResponseData,
    PaymentMethodTokenizationResult,
    StoredPaymentMethodRequestDeleteData,
    StoredPaymentMethodRequestDeleteResponseData,
    TransactionActionData,
    TransactionSessionData,
    TransactionSessionResult,
)
from ...payment.models import Payment, TransactionItem
from ...settings import WEBHOOK_SYNC_TIMEOUT
from ...thumbnail.models import Thumbnail
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...webhook.payloads import (
    generate_checkout_payload,
    generate_checkout_payload_for_tax_calculation,
    generate_collection_payload,
    generate_customer_payload,
    generate_excluded_shipping_methods_for_checkout_payload,
    generate_excluded_shipping_methods_for_order_payload,
    generate_fulfillment_payload,
    generate_invoice_payload,
    generate_list_gateways_payload,
    generate_meta,
    generate_metadata_updated_payload,
    generate_order_payload,
    generate_order_payload_for_tax_calculation,
    generate_page_payload,
    generate_payment_payload,
    generate_product_deleted_payload,
    generate_product_media_payload,
    generate_product_payload,
    generate_product_variant_payload,
    generate_product_variant_with_stock_payload,
    generate_requestor,
    generate_sale_payload,
    generate_sale_toggle_payload,
    generate_thumbnail_payload,
    generate_transaction_session_payload,
    generate_translation_payload,
)
from ...webhook.utils import get_webhooks_for_event
from ..base_plugin import BasePlugin, ExcludedShippingMethod
from .const import CACHE_EXCLUDED_SHIPPING_KEY, WEBHOOK_CACHE_DEFAULT_TIMEOUT
from .shipping import (
    get_cache_data_for_shipping_list_methods_for_checkout,
    get_excluded_shipping_data,
    parse_list_shipping_methods_response,
)
from .stored_payment_methods import (
    get_list_stored_payment_methods_data_dict,
    get_list_stored_payment_methods_from_response,
    get_response_for_payment_gateway_initialize_tokenization,
    get_response_for_payment_method_tokenization,
    get_response_for_stored_payment_method_request_delete,
    invalidate_cache_for_stored_payment_methods,
)
from .tasks import (
    send_webhook_request_async,
    trigger_all_webhooks_sync,
    trigger_transaction_request,
    trigger_webhook_sync,
    trigger_webhook_sync_if_not_cached,
    trigger_webhooks_async,
)
from .utils import (
    DEFAULT_TAX_CODE,
    DEFAULT_TAX_DESCRIPTION,
    delivery_update,
    from_payment_app_id,
    get_current_tax_app,
    get_meta_code_key,
    get_meta_description_key,
    parse_list_payment_gateways_response,
    parse_payment_action_response,
    parse_tax_data,
)

if TYPE_CHECKING:
    from ...account.models import Address, Group, User
    from ...attribute.models import Attribute, AttributeValue
    from ...channel.models import Channel
    from ...csv.models import ExportFile
    from ...discount.models import Sale, Voucher
    from ...giftcard.models import GiftCard
    from ...invoice.models import Invoice
    from ...menu.models import Menu, MenuItem
    from ...order.models import Fulfillment, Order
    from ...page.models import Page, PageType
    from ...product.models import (
        Category,
        Collection,
        Product,
        ProductMedia,
        ProductType,
        ProductVariant,
    )
    from ...shipping.interface import ShippingMethodData
    from ...shipping.models import ShippingMethod, ShippingZone
    from ...site.models import SiteSettings
    from ...tax.models import TaxClass
    from ...translation.models import Translation
    from ...warehouse.models import Stock, Warehouse
    from ...webhook.models import Webhook


CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT: Final[int] = 5 * 60  # 5 minutes


logger = logging.getLogger(__name__)


class WebhookPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.webhooks"
    PLUGIN_NAME = "Webhooks"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False

    @classmethod
    def check_plugin_id(cls, plugin_id: str) -> bool:
        is_webhook_plugin = super().check_plugin_id(plugin_id)
        if not is_webhook_plugin:
            payment_app_data = from_payment_app_id(plugin_id)
            return payment_app_data is not None
        return is_webhook_plugin

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    @staticmethod
    def _serialize_payload(data):
        return json.dumps(data, cls=CustomJsonEncoder)

    def _generate_meta(self):
        return generate_meta(requestor_data=generate_requestor(self.requestor))

    def _trigger_metadata_updated_event(self, event_type, instance):
        if webhooks := get_webhooks_for_event(event_type):
            metadata_payload_generator = partial(
                generate_metadata_updated_payload, instance, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                instance,
                self.requestor,
                legacy_data_generator=metadata_payload_generator,
            )

    def _trigger_account_request_event(
        self, event_type, user, channel_slug, token, redirect_url, new_email=None
    ):
        if webhooks := get_webhooks_for_event(event_type):
            raw_payload = {
                "id": graphene.Node.to_global_id("User", user.id),
                "token": token,
                "redirect_url": redirect_url,
            }
            data = {
                "user": user,
                "channel_slug": channel_slug,
                "token": token,
                "redirect_url": redirect_url,
            }

            if new_email:
                raw_payload["new_email"] = new_email
                data["new_email"] = new_email

            trigger_webhooks_async(
                self._serialize_payload(raw_payload),
                event_type,
                webhooks,
                data,
                self.requestor,
            )

    def _trigger_account_event(self, event_type, user):
        if webhooks := get_webhooks_for_event(event_type):
            raw_payload = {
                "id": graphene.Node.to_global_id("User", user.id),
            }
            data = {"user": user}
            trigger_webhooks_async(
                self._serialize_payload(raw_payload),
                event_type,
                webhooks,
                data,
                self.requestor,
            )

    def account_confirmed(self, user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_event(
            WebhookEventAsyncType.ACCOUNT_CONFIRMED,
            user,
        )

    def account_confirmation_requested(
        self,
        user: "User",
        channel_slug: str,
        token: str,
        redirect_url: Optional[str],
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_request_event(
            WebhookEventAsyncType.ACCOUNT_CONFIRMATION_REQUESTED,
            user,
            channel_slug,
            token,
            redirect_url,
        )

    def account_change_email_requested(
        self,
        user: "User",
        channel_slug: str,
        token: str,
        redirect_url: str,
        new_email: str,
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_request_event(
            WebhookEventAsyncType.ACCOUNT_CHANGE_EMAIL_REQUESTED,
            user,
            channel_slug,
            token,
            redirect_url,
            new_email,
        )

    def account_email_changed(
        self,
        user: "User",
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_event(
            WebhookEventAsyncType.ACCOUNT_EMAIL_CHANGED,
            user,
        )

    def account_set_password_requested(
        self,
        user: "User",
        channel_slug: str,
        token: str,
        redirect_url: str,
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_request_event(
            WebhookEventAsyncType.ACCOUNT_SET_PASSWORD_REQUESTED,
            user,
            channel_slug,
            token,
            redirect_url,
        )

    def account_delete_requested(
        self,
        user: "User",
        channel_slug: str,
        token: str,
        redirect_url: str,
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_request_event(
            WebhookEventAsyncType.ACCOUNT_DELETE_REQUESTED,
            user,
            channel_slug,
            token,
            redirect_url,
        )

    def account_deleted(self, user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_event(
            WebhookEventAsyncType.ACCOUNT_DELETED,
            user,
        )

    def _trigger_address_event(self, event_type, address):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Address", address.id),
                    "city": address.city,
                    "country": {
                        "code": address.country.code,
                        "name": address.country.name,
                    },
                    "company_name": address.company_name,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, address, self.requestor
            )

    def address_created(self, address: "Address", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_address_event(WebhookEventAsyncType.ADDRESS_CREATED, address)

    def address_updated(self, address: "Address", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_address_event(WebhookEventAsyncType.ADDRESS_UPDATED, address)

    def address_deleted(self, address: "Address", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_address_event(WebhookEventAsyncType.ADDRESS_DELETED, address)

    def _trigger_app_event(self, event_type, app):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("App", app.id),
                    "is_active": app.is_active,
                    "name": app.name,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(payload, event_type, webhooks, app, self.requestor)

    def app_installed(self, app: "App", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_app_event(WebhookEventAsyncType.APP_INSTALLED, app)

    def app_updated(self, app: "App", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_app_event(WebhookEventAsyncType.APP_UPDATED, app)

    def app_deleted(self, app: "App", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_app_event(WebhookEventAsyncType.APP_DELETED, app)

    def app_status_changed(self, app: "App", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_app_event(WebhookEventAsyncType.APP_STATUS_CHANGED, app)

    def _trigger_attribute_event(self, event_type, attribute):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Attribute", attribute.id),
                    "name": attribute.name,
                    "slug": attribute.slug,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, attribute, self.requestor
            )

    def attribute_created(self, attribute: "Attribute", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_event(
            WebhookEventAsyncType.ATTRIBUTE_CREATED, attribute
        )

    def attribute_updated(self, attribute: "Attribute", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_event(
            WebhookEventAsyncType.ATTRIBUTE_UPDATED, attribute
        )

    def attribute_deleted(self, attribute: "Attribute", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_event(
            WebhookEventAsyncType.ATTRIBUTE_DELETED, attribute
        )

    def _trigger_attribute_value_event(self, event_type, attribute_value):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id(
                        "AttributeValue", attribute_value.id
                    ),
                    "name": attribute_value.name,
                    "slug": attribute_value.slug,
                    "value": attribute_value.value,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, attribute_value, self.requestor
            )

    def attribute_value_created(
        self, attribute_value: "AttributeValue", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_value_event(
            WebhookEventAsyncType.ATTRIBUTE_VALUE_CREATED, attribute_value
        )

    def attribute_value_updated(
        self, attribute_value: "AttributeValue", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_value_event(
            WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED, attribute_value
        )

    def attribute_value_deleted(
        self, attribute_value: "AttributeValue", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_value_event(
            WebhookEventAsyncType.ATTRIBUTE_VALUE_DELETED, attribute_value
        )

    def __trigger_category_event(self, event_type, category):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Category", category.id),
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, category, self.requestor
            )

    def category_created(self, category: "Category", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_category_event(WebhookEventAsyncType.CATEGORY_CREATED, category)

    def category_updated(self, category: "Category", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_category_event(WebhookEventAsyncType.CATEGORY_UPDATED, category)

    def category_deleted(self, category: "Category", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_category_event(WebhookEventAsyncType.CATEGORY_DELETED, category)

    def __trigger_channel_event(self, event_type, channel):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Channel", channel.id),
                    "is_active": channel.is_active,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, channel, self.requestor
            )

    def channel_created(self, channel: "Channel", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(WebhookEventAsyncType.CHANNEL_CREATED, channel)

    def channel_updated(self, channel: "Channel", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(WebhookEventAsyncType.CHANNEL_UPDATED, channel)

    def channel_deleted(self, channel: "Channel", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(WebhookEventAsyncType.CHANNEL_DELETED, channel)

    def channel_status_changed(self, channel: "Channel", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(
            WebhookEventAsyncType.CHANNEL_STATUS_CHANGED, channel
        )

    def channel_metadata_updated(
        self, channel: "Channel", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(
            WebhookEventAsyncType.CHANNEL_METADATA_UPDATED, channel
        )

    def _trigger_gift_card_event(self, event_type, gift_card: "GiftCard"):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
                    "is_active": gift_card.is_active,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, gift_card, self.requestor
            )

    def gift_card_created(self, gift_card: "GiftCard", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_gift_card_event(
            WebhookEventAsyncType.GIFT_CARD_CREATED, gift_card
        )

    def gift_card_updated(self, gift_card: "GiftCard", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_gift_card_event(
            WebhookEventAsyncType.GIFT_CARD_UPDATED, gift_card
        )

    def gift_card_deleted(self, gift_card: "GiftCard", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_gift_card_event(
            WebhookEventAsyncType.GIFT_CARD_DELETED, gift_card
        )

    def gift_card_sent(
        self,
        gift_card: "GiftCard",
        channel_slug: str,
        sent_to_email: str,
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value

        event_type = WebhookEventAsyncType.GIFT_CARD_SENT
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
                    "is_active": gift_card.is_active,
                    "channel_slug": channel_slug,
                    "sent_to_email": sent_to_email,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                {
                    "gift_card": gift_card,
                    "channel_slug": channel_slug,
                    "sent_to_email": sent_to_email,
                },
                self.requestor,
            )

    def gift_card_metadata_updated(
        self, gift_card: "GiftCard", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.GIFT_CARD_METADATA_UPDATED, gift_card
        )

    def gift_card_status_changed(
        self, gift_card: "GiftCard", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_gift_card_event(
            WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED, gift_card
        )

    def _trigger_export_event(self, event_type: str, export: "ExportFile"):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("ExportFile", export.id),
                    "export": get_default_export_payload(export),
                    "csv_link": build_absolute_uri(export.content_file.url),
                    "recipient_email": export.user.email if export.user else None,
                }
            )
            trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                export,
                self.requestor,
            )

    def gift_card_export_completed(
        self, export: "ExportFile", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_export_event(
            WebhookEventAsyncType.GIFT_CARD_EXPORT_COMPLETED,
            export,
        )

    def order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def _trigger_menu_event(self, event_type, menu):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Menu", menu.id),
                    "slug": menu.slug,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(payload, event_type, webhooks, menu, self.requestor)

    def menu_created(self, menu: "Menu", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_menu_event(WebhookEventAsyncType.MENU_CREATED, menu)

    def menu_updated(self, menu: "Menu", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_menu_event(WebhookEventAsyncType.MENU_UPDATED, menu)

    def menu_deleted(self, menu: "Menu", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_menu_event(WebhookEventAsyncType.MENU_DELETED, menu)

    def __trigger_menu_item_event(self, event_type, menu_item):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("MenuItem", menu_item.id),
                    "name": menu_item.name,
                    "menu": {
                        "id": graphene.Node.to_global_id("Menu", menu_item.menu_id)
                    },
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, menu_item, self.requestor
            )

    def menu_item_created(self, menu_item: "MenuItem", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_menu_item_event(
            WebhookEventAsyncType.MENU_ITEM_CREATED, menu_item
        )

    def menu_item_updated(self, menu_item: "MenuItem", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_menu_item_event(
            WebhookEventAsyncType.MENU_ITEM_UPDATED, menu_item
        )

    def menu_item_deleted(self, menu_item: "MenuItem", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_menu_item_event(
            WebhookEventAsyncType.MENU_ITEM_DELETED, menu_item
        )

    def order_confirmed(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_CONFIRMED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def order_fully_paid(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_FULLY_PAID
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def order_paid(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_PAID
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def order_refunded(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_REFUNDED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def order_fully_refunded(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_FULLY_REFUNDED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def order_updated(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def order_expired(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_EXPIRED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def sale_created(
        self,
        sale: "Sale",
        current_catalogue: DefaultDict[str, Set[str]],
        previous_value: Any,
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.SALE_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            sale_data_generator = partial(
                generate_sale_payload,
                sale,
                previous_catalogue=None,
                current_catalogue=current_catalogue,
                requestor=self.requestor,
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                sale,
                self.requestor,
                legacy_data_generator=sale_data_generator,
            )

    def sale_updated(
        self,
        sale: "Sale",
        previous_catalogue: DefaultDict[str, Set[str]],
        current_catalogue: DefaultDict[str, Set[str]],
        previous_value: Any,
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.SALE_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            sale_data_generator = partial(
                generate_sale_payload,
                sale,
                previous_catalogue,
                current_catalogue,
                self.requestor,
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                sale,
                self.requestor,
                legacy_data_generator=sale_data_generator,
            )

    def sale_deleted(
        self,
        sale: "Sale",
        previous_catalogue: DefaultDict[str, Set[str]],
        previous_value: Any,
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.SALE_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            sale_data_generator = partial(
                generate_sale_payload,
                sale,
                previous_catalogue=previous_catalogue,
                requestor=self.requestor,
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                sale,
                self.requestor,
                legacy_data_generator=sale_data_generator,
            )

    def sale_toggle(
        self,
        sale: "Sale",
        catalogue: DefaultDict[str, Set[str]],
        previous_value: Any,
    ):
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.SALE_TOGGLE
        if webhooks := get_webhooks_for_event(event_type):
            sale_data_generator = partial(
                generate_sale_toggle_payload,
                sale,
                catalogue=catalogue,
                requestor=self.requestor,
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                sale,
                self.requestor,
                legacy_data_generator=sale_data_generator,
            )

    def invoice_request(
        self,
        order: "Order",
        invoice: "Invoice",
        number: Optional[str],
        previous_value: Any,
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.INVOICE_REQUESTED
        if webhooks := get_webhooks_for_event(event_type):
            invoice_data_generator = partial(
                generate_invoice_payload, invoice, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                invoice,
                self.requestor,
                legacy_data_generator=invoice_data_generator,
            )

    def invoice_delete(self, invoice: "Invoice", previous_value: Any):
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.INVOICE_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            invoice_data_generator = partial(
                generate_invoice_payload, invoice, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                invoice,
                self.requestor,
                legacy_data_generator=invoice_data_generator,
            )

    def invoice_sent(self, invoice: "Invoice", email: str, previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.INVOICE_SENT
        if webhooks := get_webhooks_for_event(event_type):
            invoice_data_generator = partial(
                generate_invoice_payload, invoice, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                invoice,
                self.requestor,
                legacy_data_generator=invoice_data_generator,
            )

    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_CANCELLED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def order_fulfilled(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_FULFILLED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def order_metadata_updated(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.ORDER_METADATA_UPDATED, order
        )

    def order_bulk_created(self, orders: List["Order"], previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_BULK_CREATED
        if webhooks := get_webhooks_for_event(event_type):

            def generate_bulk_order_payload():
                return [
                    generate_order_payload(order, self.requestor) for order in orders
                ]

            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                orders,
                self.requestor,
                legacy_data_generator=generate_bulk_order_payload,
            )

    def draft_order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.DRAFT_ORDER_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def draft_order_updated(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.DRAFT_ORDER_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def draft_order_deleted(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.DRAFT_ORDER_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
            )

    def fulfillment_created(
        self,
        fulfillment: "Fulfillment",
        notify_customer: bool = True,
        previous_value: Optional[Any] = None,
    ):
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.FULFILLMENT_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            fulfillment_data_generator = partial(
                generate_fulfillment_payload, fulfillment, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                {
                    "notify_customer": notify_customer,
                    "fulfillment": fulfillment,
                },
                self.requestor,
                legacy_data_generator=fulfillment_data_generator,
            )

    def fulfillment_canceled(self, fulfillment: "Fulfillment", previous_value):
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.FULFILLMENT_CANCELED
        if webhooks := get_webhooks_for_event(event_type):
            fulfillment_data_generator = partial(
                generate_fulfillment_payload, fulfillment, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                fulfillment,
                self.requestor,
                legacy_data_generator=fulfillment_data_generator,
            )

    def fulfillment_approved(
        self,
        fulfillment: "Fulfillment",
        notify_customer: Optional[bool] = True,
        previous_value: Optional[Any] = None,
    ):
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.FULFILLMENT_APPROVED
        if webhooks := get_webhooks_for_event(event_type):
            fulfillment_data_generator = partial(
                generate_fulfillment_payload, fulfillment, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                {
                    "fulfillment": fulfillment,
                    "notify_customer": notify_customer,
                },
                self.requestor,
                legacy_data_generator=fulfillment_data_generator,
            )

    def fulfillment_metadata_updated(self, fulfillment: "Fulfillment", previous_value):
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.FULFILLMENT_METADATA_UPDATED, fulfillment
        )

    def tracking_number_updated(self, fulfillment: "Fulfillment", previous_value):
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.FULFILLMENT_TRACKING_NUMBER_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            fulfillment_data = generate_fulfillment_payload(fulfillment, self.requestor)
            trigger_webhooks_async(
                fulfillment_data, event_type, webhooks, fulfillment, self.requestor
            )

    def customer_created(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CUSTOMER_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            customer_data_generator = partial(
                generate_customer_payload, customer, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                customer,
                self.requestor,
                legacy_data_generator=customer_data_generator,
            )

    def customer_updated(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CUSTOMER_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            customer_data_generator = partial(
                generate_customer_payload, customer, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                customer,
                self.requestor,
                legacy_data_generator=customer_data_generator,
            )

    def customer_deleted(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CUSTOMER_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            customer_data_generator = partial(
                generate_customer_payload, customer, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                customer,
                self.requestor,
                legacy_data_generator=customer_data_generator,
            )

    def customer_metadata_updated(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED, customer
        )

    def collection_created(self, collection: "Collection", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.COLLECTION_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            collection_data_generator = partial(
                generate_collection_payload, collection, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                collection,
                self.requestor,
                legacy_data_generator=collection_data_generator,
            )

    def collection_updated(self, collection: "Collection", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.COLLECTION_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            collection_data_generator = partial(
                generate_collection_payload, collection, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                collection,
                self.requestor,
                legacy_data_generator=collection_data_generator,
            )

    def collection_deleted(self, collection: "Collection", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.COLLECTION_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            collection_data_generator = partial(
                generate_collection_payload, collection, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                collection,
                self.requestor,
                legacy_data_generator=collection_data_generator,
            )

    def collection_metadata_updated(
        self, collection: "Collection", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.COLLECTION_METADATA_UPDATED, collection
        )

    def product_created(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            product_data_generator = partial(
                generate_product_payload, product, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product,
                self.requestor,
                legacy_data_generator=product_data_generator,
            )

    def product_updated(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            product_data_generator = partial(
                generate_product_payload, product, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product,
                self.requestor,
                legacy_data_generator=product_data_generator,
            )

    def product_metadata_updated(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value

        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.PRODUCT_METADATA_UPDATED, product
        )

    def product_export_completed(
        self, export: "ExportFile", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_export_event(
            WebhookEventAsyncType.PRODUCT_EXPORT_COMPLETED,
            export,
        )

    def product_deleted(
        self, product: "Product", variants: List[int], previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            product_data_generator = partial(
                generate_product_deleted_payload, product, variants, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product,
                self.requestor,
                legacy_data_generator=product_data_generator,
            )

    def product_media_created(self, media: "ProductMedia", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_MEDIA_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            media_data_generator = partial(generate_product_media_payload, media)
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                media,
                self.requestor,
                legacy_data_generator=media_data_generator,
            )

    def product_media_updated(self, media: "ProductMedia", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_MEDIA_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            media_data_generator = partial(generate_product_media_payload, media)
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                media,
                self.requestor,
                legacy_data_generator=media_data_generator,
            )

    def product_media_deleted(self, media: "ProductMedia", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_MEDIA_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            media_data_generator = partial(generate_product_media_payload, media)
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                media,
                self.requestor,
                legacy_data_generator=media_data_generator,
            )

    def product_variant_created(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            product_variant_data_generator = partial(
                generate_product_variant_payload, [product_variant], self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product_variant,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )

    def product_variant_updated(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            product_variant_data_generator = partial(
                generate_product_variant_payload, [product_variant], self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product_variant,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )

    def product_variant_deleted(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            product_variant_data_generator = partial(
                generate_product_variant_payload, [product_variant], self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product_variant,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )

    def product_variant_metadata_updated(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_METADATA_UPDATED, product_variant
        )

    def product_variant_out_of_stock(self, stock: "Stock", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK
        if webhooks := get_webhooks_for_event(event_type):
            product_variant_data_generator = partial(
                generate_product_variant_with_stock_payload, [stock]
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                stock,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )

    def product_variant_back_in_stock(self, stock: "Stock", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK
        if webhooks := get_webhooks_for_event(event_type):
            product_variant_data_generator = partial(
                generate_product_variant_with_stock_payload, [stock], self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                stock,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )

    def product_variant_stock_updated(self, stock: "Stock", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            product_variant_data_generator = (
                generate_product_variant_with_stock_payload([stock], self.requestor)
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                stock,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )

    def checkout_created(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CHECKOUT_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            checkout_data_generator = partial(
                generate_checkout_payload, checkout, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                checkout,
                self.requestor,
                legacy_data_generator=checkout_data_generator,
            )

    def checkout_updated(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            checkout_data_generator = partial(
                generate_checkout_payload, checkout, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                checkout,
                self.requestor,
                legacy_data_generator=checkout_data_generator,
            )

    def checkout_fully_paid(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CHECKOUT_FULLY_PAID
        if webhooks := get_webhooks_for_event(event_type):
            checkout_data_generator = partial(
                generate_checkout_payload, checkout, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                checkout,
                self.requestor,
                legacy_data_generator=checkout_data_generator,
            )

    def checkout_metadata_updated(
        self, checkout: "Checkout", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED, checkout
        )

    def notify(
        self, event: Union[NotifyEventType, str], payload: dict, previous_value
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.NOTIFY_USER
        if webhooks := get_webhooks_for_event(event_type):
            data = self._serialize_payload(
                {
                    "notify_event": event,
                    "payload": payload,
                    "meta": generate_meta(
                        requestor_data=generate_requestor(self.requestor)
                    ),
                }
            )
            if event not in NotifyEventType.CHOICES:
                logger.info(f"Webhook {event_type} triggered for {event} notify event.")
            trigger_webhooks_async(data, event_type, webhooks)

    def page_created(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PAGE_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            page_data_generator = partial(generate_page_payload, page, self.requestor)
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                page,
                self.requestor,
                legacy_data_generator=page_data_generator,
            )

    def page_updated(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PAGE_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            page_data_generator = partial(generate_page_payload, page, self.requestor)
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                page,
                self.requestor,
                legacy_data_generator=page_data_generator,
            )

    def page_deleted(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PAGE_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            page_data_generator = partial(generate_page_payload, page, self.requestor)
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                page,
                self.requestor,
                legacy_data_generator=page_data_generator,
            )

    def _trigger_page_type_event(self, event_type, page_type):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("PageType", page_type.id),
                    "name": page_type.name,
                    "slug": page_type.slug,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, page_type, self.requestor
            )

    def page_type_created(self, page_type: "PageType", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        self._trigger_page_type_event(
            WebhookEventAsyncType.PAGE_TYPE_CREATED, page_type
        )

    def page_type_updated(self, page_type: "PageType", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        self._trigger_page_type_event(
            WebhookEventAsyncType.PAGE_TYPE_UPDATED, page_type
        )

    def page_type_deleted(self, page_type: "PageType", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        self._trigger_page_type_event(
            WebhookEventAsyncType.PAGE_TYPE_DELETED, page_type
        )

    def _trigger_permission_group_event(self, event_type, group):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Group", group.id),
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(payload, event_type, webhooks, group, self.requestor)

    def permission_group_created(self, group: "Group", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        self._trigger_permission_group_event(
            WebhookEventAsyncType.PERMISSION_GROUP_CREATED, group
        )

    def permission_group_updated(self, group: "Group", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        self._trigger_permission_group_event(
            WebhookEventAsyncType.PERMISSION_GROUP_UPDATED, group
        )

    def permission_group_deleted(self, group: "Group", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        self._trigger_permission_group_event(
            WebhookEventAsyncType.PERMISSION_GROUP_DELETED, group
        )

    def _trigger_shipping_price_event(self, event_type, shipping_method):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id(
                        "ShippingMethodType", shipping_method.id
                    ),
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, shipping_method, self.requestor
            )

    def shipping_price_created(
        self, shipping_method: "ShippingMethod", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_price_event(
            WebhookEventAsyncType.SHIPPING_PRICE_CREATED, shipping_method
        )

    def shipping_price_updated(
        self, shipping_method: "ShippingMethod", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_price_event(
            WebhookEventAsyncType.SHIPPING_PRICE_UPDATED, shipping_method
        )

    def shipping_price_deleted(
        self, shipping_method: "ShippingMethod", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value

        self._trigger_shipping_price_event(
            WebhookEventAsyncType.SHIPPING_PRICE_DELETED, shipping_method
        )

    def _trigger_shipping_zone_event(self, event_type, shipping_zone):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("ShippingZone", shipping_zone.id),
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, shipping_zone, self.requestor
            )

    def shipping_zone_created(
        self, shipping_zone: "ShippingZone", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_zone_event(
            WebhookEventAsyncType.SHIPPING_ZONE_CREATED, shipping_zone
        )

    def shipping_zone_updated(
        self, shipping_zone: "ShippingZone", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_zone_event(
            WebhookEventAsyncType.SHIPPING_ZONE_UPDATED, shipping_zone
        )

    def shipping_zone_deleted(
        self, shipping_zone: "ShippingZone", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_zone_event(
            WebhookEventAsyncType.SHIPPING_ZONE_DELETED, shipping_zone
        )

    def shipping_zone_metadata_updated(
        self, shipping_zone: "ShippingZone", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.SHIPPING_ZONE_METADATA_UPDATED, shipping_zone
        )

    def _trigger_staff_event(self, event_type, staff_user):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("User", staff_user.id),
                    "email": staff_user.email,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, staff_user, self.requestor
            )

    def staff_created(self, staff_user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_staff_event(WebhookEventAsyncType.STAFF_CREATED, staff_user)

    def staff_updated(self, staff_user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_staff_event(WebhookEventAsyncType.STAFF_UPDATED, staff_user)

    def staff_deleted(self, staff_user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_staff_event(WebhookEventAsyncType.STAFF_DELETED, staff_user)

    def staff_set_password_requested(
        self,
        user: "User",
        channel_slug: str,
        token: str,
        redirect_url: str,
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_request_event(
            WebhookEventAsyncType.STAFF_SET_PASSWORD_REQUESTED,
            user,
            channel_slug,
            token,
            redirect_url,
        )

    def thumbnail_created(
        self,
        thumbnail: Thumbnail,
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.THUMBNAIL_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            thumbnail_data_generator = partial(generate_thumbnail_payload, thumbnail)
            trigger_webhooks_async(
                data=None,
                event_type=event_type,
                webhooks=webhooks,
                subscribable_object=thumbnail,
                legacy_data_generator=thumbnail_data_generator,
            )

    def translation_created(self, translation: "Translation", previous_value: Any):
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.TRANSLATION_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            translation_data_generator = partial(
                generate_translation_payload, translation, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                translation,
                self.requestor,
                legacy_data_generator=translation_data_generator,
            )

    def translation_updated(self, translation: "Translation", previous_value: Any):
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            translation_data_generator = partial(
                generate_translation_payload, translation, self.requestor
            )
            trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                translation,
                self.requestor,
                legacy_data_generator=translation_data_generator,
            )

    def _trigger_warehouse_event(self, event_type, warehouse):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Warehouse", warehouse.id),
                    "name": warehouse.name,
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, warehouse, self.requestor
            )

    def warehouse_created(self, warehouse: "Warehouse", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_warehouse_event(
            WebhookEventAsyncType.WAREHOUSE_CREATED, warehouse
        )

    def warehouse_updated(self, warehouse: "Warehouse", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_warehouse_event(
            WebhookEventAsyncType.WAREHOUSE_UPDATED, warehouse
        )

    def warehouse_deleted(self, warehouse: "Warehouse", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_warehouse_event(
            WebhookEventAsyncType.WAREHOUSE_DELETED, warehouse
        )

    def warehouse_metadata_updated(
        self, warehouse: "Warehouse", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.WAREHOUSE_METADATA_UPDATED, warehouse
        )

    def _trigger_voucher_event(self, event_type, voucher):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Voucher", voucher.id),
                    "name": voucher.name,
                    "code": voucher.code,
                    "meta": self._generate_meta(),
                }
            )
            trigger_webhooks_async(
                payload, event_type, webhooks, voucher, self.requestor
            )

    def voucher_created(self, voucher: "Voucher", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_voucher_event(WebhookEventAsyncType.VOUCHER_CREATED, voucher)

    def voucher_updated(self, voucher: "Voucher", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_voucher_event(WebhookEventAsyncType.VOUCHER_UPDATED, voucher)

    def voucher_deleted(self, voucher: "Voucher", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_voucher_event(WebhookEventAsyncType.VOUCHER_DELETED, voucher)

    def voucher_metadata_updated(
        self, voucher: "Voucher", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.VOUCHER_METADATA_UPDATED, voucher
        )

    def shop_metadata_updated(self, shop: "SiteSettings", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.SHOP_METADATA_UPDATED, shop
        )

    def event_delivery_retry(self, delivery: "EventDelivery", previous_value: Any):
        if not self.active:
            return previous_value
        delivery_update(delivery, status=EventDeliveryStatus.PENDING)
        send_webhook_request_async.delay(delivery.pk)

    def stored_payment_method_request_delete(
        self,
        request_delete_data: "StoredPaymentMethodRequestDeleteData",
        previous_value: "StoredPaymentMethodRequestDeleteResponseData",
    ) -> "StoredPaymentMethodRequestDeleteResponseData":
        if not self.active:
            return previous_value

        app_data = from_payment_app_id(request_delete_data.payment_method_id)
        if not app_data or not app_data.app_identifier:
            return previous_value

        event_type = WebhookEventSyncType.STORED_PAYMENT_METHOD_DELETE_REQUESTED
        webhook = get_webhooks_for_event(
            event_type, apps_identifier=[app_data.app_identifier]
        ).first()

        if not webhook:
            return previous_value

        payload = self._serialize_payload(
            {
                "payment_method_id": app_data.name,
                "user_id": graphene.Node.to_global_id(
                    "User", request_delete_data.user.id
                ),
                "channel_slug": request_delete_data.channel.slug,
            }
        )

        response_data = trigger_webhook_sync(
            event_type,
            payload,
            webhook,
            subscribable_object=StoredPaymentMethodRequestDeleteData(
                payment_method_id=app_data.name,
                user=request_delete_data.user,
                channel=request_delete_data.channel,
            ),
            timeout=WEBHOOK_SYNC_TIMEOUT,
        )
        if response_data:
            invalidate_cache_for_stored_payment_methods(
                request_delete_data.user.id,
                request_delete_data.channel.slug,
                app_data.app_identifier,
            )

        return get_response_for_stored_payment_method_request_delete(response_data)

    def list_stored_payment_methods(
        self,
        list_payment_method_data: "ListStoredPaymentMethodsRequestData",
        previous_value: list["PaymentMethodData"],
    ) -> list["PaymentMethodData"]:
        if not self.active:
            return previous_value

        event_type = WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS

        if webhooks := get_webhooks_for_event(event_type):
            payload_dict = get_list_stored_payment_methods_data_dict(
                list_payment_method_data.user.id, list_payment_method_data.channel.slug
            )
            payload = self._serialize_payload(payload_dict)
            for webhook in webhooks:
                if not webhook.app.identifier:
                    continue
                response_data = trigger_webhook_sync_if_not_cached(
                    event_type,
                    payload,
                    webhook,
                    cache_data=payload_dict,
                    subscribable_object=list_payment_method_data,
                    request_timeout=WEBHOOK_SYNC_TIMEOUT,
                    cache_timeout=WEBHOOK_CACHE_DEFAULT_TIMEOUT,
                )
                if response_data:
                    previous_value.extend(
                        get_list_stored_payment_methods_from_response(
                            webhook.app,
                            response_data,
                            list_payment_method_data.channel.currency_code,
                        )
                    )
        return previous_value

    def _handle_payment_tokenization_request(
        self,
        webhook: "Webhook",
        event_type: str,
        request_data: PaymentMethodTokenizationBaseRequestData,
        additional_legacy_payload_data: Optional[dict] = None,
    ) -> Optional[dict]:
        payload_data = {
            "user_id": graphene.Node.to_global_id("User", request_data.user.id),
            "channel_slug": request_data.channel.slug,
            "data": request_data.data,
        }
        if additional_legacy_payload_data:
            payload_data.update(additional_legacy_payload_data)

        payload = self._serialize_payload(payload_data)
        response_data = trigger_webhook_sync(
            event_type,
            payload,
            webhook,
            subscribable_object=request_data,
            timeout=WEBHOOK_SYNC_TIMEOUT,
        )
        return response_data

    def payment_gateway_initialize_tokenization(
        self,
        request_data: "PaymentGatewayInitializeTokenizationRequestData",
        previous_value: "PaymentGatewayInitializeTokenizationResponseData",
    ) -> "PaymentGatewayInitializeTokenizationResponseData":
        if not self.active:
            return previous_value

        event_type = (
            WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION
        )
        webhook = get_webhooks_for_event(
            event_type, apps_identifier=[request_data.app_identifier]
        ).first()

        if not webhook:
            return previous_value

        response_data = self._handle_payment_tokenization_request(
            event_type=event_type, webhook=webhook, request_data=request_data
        )
        return get_response_for_payment_gateway_initialize_tokenization(response_data)

    def _handle_payment_method_tokenization(
        self,
        app_identifier: str,
        event_type: str,
        request_data: PaymentMethodTokenizationBaseRequestData,
        previous_value: "PaymentMethodTokenizationResponseData",
        additional_legacy_payload_data: Optional[dict] = None,
    ):
        webhook = get_webhooks_for_event(
            event_type, apps_identifier=[app_identifier]
        ).first()

        if not webhook:
            return previous_value

        response_data = self._handle_payment_tokenization_request(
            event_type=event_type,
            webhook=webhook,
            request_data=request_data,
            additional_legacy_payload_data=additional_legacy_payload_data,
        )

        response = get_response_for_payment_method_tokenization(
            response_data, webhook.app
        )
        if response.result in [
            PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED,
            PaymentMethodTokenizationResult.PENDING,
        ]:
            invalidate_cache_for_stored_payment_methods(
                request_data.user.id,
                request_data.channel.slug,
                app_identifier,
            )
        return response

    def payment_method_initialize_tokenization(
        self,
        request_data: "PaymentMethodInitializeTokenizationRequestData",
        previous_value: "PaymentMethodTokenizationResponseData",
    ) -> "PaymentMethodTokenizationResponseData":
        if not self.active:
            return previous_value

        event_type = WebhookEventSyncType.PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION

        return self._handle_payment_method_tokenization(
            app_identifier=request_data.app_identifier,
            event_type=event_type,
            request_data=request_data,
            previous_value=previous_value,
            additional_legacy_payload_data={
                "payment_flow_to_support": request_data.payment_flow_to_support
            },
        )

    def payment_method_process_tokenization(
        self,
        request_data: "PaymentMethodProcessTokenizationRequestData",
        previous_value: "PaymentMethodTokenizationResponseData",
    ) -> "PaymentMethodTokenizationResponseData":
        if not self.active:
            return previous_value

        app_data = from_payment_app_id(request_data.id)

        if not app_data or not app_data.app_identifier:
            return previous_value

        request_data.id = app_data.name

        event_type = WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION
        return self._handle_payment_method_tokenization(
            app_identifier=app_data.app_identifier,
            event_type=event_type,
            request_data=request_data,
            previous_value=previous_value,
            additional_legacy_payload_data={"id": request_data.id},
        )

    def _request_transaction_action(
        self,
        transaction_data: "TransactionActionData",
        event_type: str,
        previous_value: Any,
    ) -> None:
        if not self.active:
            return previous_value

        if not transaction_data.transaction_app_owner:
            logger.warning(
                f"Transaction request skipped for "
                f"{transaction_data.transaction.psp_reference}. "
                f"Missing relation to App."
            )
            return None

        if not transaction_data.event:
            logger.warning(
                f"Transaction request skipped for "
                f"{transaction_data.transaction.psp_reference}. "
                f"Missing relation to TransactionEvent."
            )
            return None

        trigger_transaction_request(transaction_data, event_type, self.requestor)
        return None

    def transaction_charge_requested(
        self, transaction_data: "TransactionActionData", previous_value: Any
    ):
        return self._request_transaction_action(
            transaction_data,
            WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
            previous_value,
        )

    def transaction_refund_requested(
        self, transaction_data: "TransactionActionData", previous_value: Any
    ):
        return self._request_transaction_action(
            transaction_data,
            WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
            previous_value,
        )

    def transaction_cancelation_requested(
        self, transaction_data: "TransactionActionData", previous_value: Any
    ):
        return self._request_transaction_action(
            transaction_data,
            WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED,
            previous_value,
        )

    def __run_payment_webhook(
        self,
        event_type: str,
        transaction_kind: str,
        payment_information: "PaymentData",
        previous_value,
        **kwargs,
    ) -> "GatewayResponse":
        """Trigger payment webhook event.

        Only one app should have defined the webhook for payment event.
        If more than one app has, the webhook is sent only for the first one.
        """
        if not self.active:
            return previous_value

        apps = None
        payment_app_data = from_payment_app_id(payment_information.gateway)

        if payment_app_data is not None:
            if payment_app_data.app_identifier:
                apps = App.objects.for_event_type(event_type).filter(
                    identifier=payment_app_data.app_identifier
                )
            else:
                apps = App.objects.for_event_type(event_type).filter(
                    pk=payment_app_data.app_pk
                )

        if not apps:
            logger.warning(
                "Payment webhook for event %r failed - no active app found: %r",
                event_type,
                payment_information.gateway,
            )
            raise PaymentError(
                f"Payment method {payment_information.gateway} is not available: "
                "app not found."
            )

        webhook_payload = generate_payment_payload(payment_information)
        payment = Payment.objects.filter(id=payment_information.payment_id).first()
        if not payment:
            raise PaymentError(
                f"Payment with id: {payment_information.payment_id} not found."
            )

        for app in apps:
            webhook = get_webhooks_for_event(event_type, app.webhooks.all()).first()
            if not webhook:
                raise PaymentError(f"No payment webhook found for event: {event_type}.")
            response_data = trigger_webhook_sync(
                event_type, webhook_payload, webhook, subscribable_object=payment
            )
            if response_data is None:
                continue

            return parse_payment_action_response(
                payment_information, response_data, transaction_kind
            )

        raise PaymentError(
            f"Payment method {payment_information.gateway} is not available: "
            "no response from the app."
        )

    def _payment_gateway_initialize_session_for_single_webhook(
        self,
        webhook: "Webhook",
        gateways: dict[str, "PaymentGatewayData"],
        response_gateway: dict[str, "PaymentGatewayData"],
        amount: Decimal,
        source_object: Union["Order", "Checkout"],
        request: SaleorContext,
    ):
        if not webhook.app.identifier:
            logger.debug(
                "Skipping app with id %s as identifier is not provided.",
                webhook.app.pk,
            )
            return
        if webhook.app.identifier in response_gateway:
            logger.debug(
                "Skipping next call for %s as app has been already processed.",
                webhook.app.identifier,
            )
            return

        gateway = gateways.get(webhook.app.identifier)
        gateway_data = None
        if gateway:
            gateway_data = gateway.data

        source_object_id = graphene.Node.to_global_id(
            source_object.__class__.__name__, source_object.pk
        )
        payload = {"id": source_object_id, "data": gateway_data, "amount": amount}
        subscribable_object = (source_object, gateway_data, amount)
        response_data = trigger_webhook_sync(
            event_type=WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION,
            payload=json.dumps(payload, cls=CustomJsonEncoder),
            webhook=webhook,
            subscribable_object=subscribable_object,
            request=request,
        )
        error_msg = None
        if response_data is None:
            error_msg = "Unable to process a payment gateway response."
        response_gateway[webhook.app.identifier] = PaymentGatewayData(
            app_identifier=webhook.app.identifier,
            data=response_data,
            error=error_msg,
        )

    def payment_gateway_initialize_session(
        self,
        amount: Decimal,
        payment_gateways: Optional[list[PaymentGatewayData]],
        source_object: Union["Order", "Checkout"],
        previous_value,
    ) -> list[PaymentGatewayData]:
        if not self.active:
            return previous_value
        response_gateway: dict[str, PaymentGatewayData] = {}
        apps_identifiers = None

        gateways = {}
        if payment_gateways:
            gateways = {gateway.app_identifier: gateway for gateway in payment_gateways}
            apps_identifiers = list(gateways.keys())

        webhooks = get_webhooks_for_event(
            WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION,
            apps_identifier=apps_identifiers,
        )

        request = initialize_request(
            self.requestor,
            sync_event=True,
            event_type=WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION,
        )

        for webhook in webhooks:
            self._payment_gateway_initialize_session_for_single_webhook(
                webhook=webhook,
                gateways=gateways,
                response_gateway=response_gateway,
                amount=amount,
                source_object=source_object,
                request=request,
            )
        return list(response_gateway.values())

    def _transaction_session_base(
        self, transaction_session_data: TransactionSessionData, webhook_event: str
    ):
        if not transaction_session_data.payment_gateway_data.app_identifier:
            error = "Missing app identifier"
            return TransactionSessionResult(
                app_identifier=transaction_session_data.payment_gateway_data.app_identifier,
                error=error,
            )
        webhook = get_webhooks_for_event(
            webhook_event,
            apps_identifier=[
                transaction_session_data.payment_gateway_data.app_identifier
            ],
        ).first()
        if not webhook:
            error = (
                "Unable to find an active webhook for "
                f"`{webhook_event.upper()}` event."
            )
            return TransactionSessionResult(
                app_identifier=transaction_session_data.payment_gateway_data.app_identifier,
                error=error,
            )

        payload = generate_transaction_session_payload(
            transaction_session_data.action,
            transaction_session_data.transaction,
            transaction_session_data.source_object,
            transaction_session_data.payment_gateway_data,
        )

        response_data = trigger_webhook_sync(
            event_type=webhook_event,
            payload=payload,
            webhook=webhook,
            subscribable_object=transaction_session_data,
        )
        error_msg = None
        if response_data is None:
            error_msg = "Unable to parse a transaction initialize response."
        return TransactionSessionResult(
            app_identifier=transaction_session_data.payment_gateway_data.app_identifier,
            response=response_data,
            error=error_msg,
        )

    def transaction_initialize_session(
        self, transaction_session_data: TransactionSessionData, previous_value
    ) -> TransactionSessionResult:
        if not self.active:
            return previous_value
        return self._transaction_session_base(
            transaction_session_data,
            WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION,
        )

    def transaction_process_session(
        self, transaction_session_data: TransactionSessionData, previous_value
    ) -> TransactionSessionResult:
        if not self.active:
            return previous_value
        return self._transaction_session_base(
            transaction_session_data, WebhookEventSyncType.TRANSACTION_PROCESS_SESSION
        )

    def token_is_required_as_payment_input(self, previous_value):
        return False

    def get_payment_gateways(
        self,
        currency: Optional[str],
        checkout_info: Optional["CheckoutInfo"],
        checkout_lines: Optional[Iterable["CheckoutLineInfo"]],
        previous_value,
        **kwargs
    ) -> List["PaymentGateway"]:
        gateways = []
        checkout = None
        if checkout_info:
            checkout = checkout_info.checkout
        event_type = WebhookEventSyncType.PAYMENT_LIST_GATEWAYS
        webhooks = get_webhooks_for_event(event_type)
        for webhook in webhooks:
            if not webhook:
                raise PaymentError(f"No payment webhook found for event: {event_type}.")

            response_data = trigger_webhook_sync(
                event_type=event_type,
                payload=generate_list_gateways_payload(currency, checkout),
                webhook=webhook,
                subscribable_object=checkout,
            )
            if response_data:
                app_gateways = parse_list_payment_gateways_response(
                    response_data, webhook.app
                )
                if currency:
                    app_gateways = [
                        gtw for gtw in app_gateways if currency in gtw.currencies
                    ]
                gateways.extend(app_gateways)
        currency = checkout.currency if checkout else currency
        if currency:
            webhooks = get_webhooks_for_event(
                WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION
            )
            for webhook in webhooks:
                app = webhook.app
                if not app or not app.identifier:
                    continue
                name = app.name or ""
                gateways.append(
                    PaymentGateway(
                        id=app.identifier,
                        name=name,
                        currencies=[
                            currency,
                        ],
                        config=[],
                    )
                )
        return gateways

    def transaction_item_metadata_updated(
        self, transaction_item: "TransactionItem", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.TRANSACTION_ITEM_METADATA_UPDATED, transaction_item
        )

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            previous_value,
            **kwargs,
        )

    def capture_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_CAPTURE,
            TransactionKind.CAPTURE,
            payment_information,
            previous_value,
            **kwargs,
        )

    def refund_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_REFUND,
            TransactionKind.REFUND,
            payment_information,
            previous_value,
            **kwargs,
        )

    def void_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_VOID,
            TransactionKind.VOID,
            payment_information,
            previous_value,
            **kwargs,
        )

    def confirm_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_CONFIRM,
            TransactionKind.CONFIRM,
            payment_information,
            previous_value,
            **kwargs,
        )

    def process_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventSyncType.PAYMENT_PROCESS,
            TransactionKind.CAPTURE,
            payment_information,
            previous_value,
            **kwargs,
        )

    def get_taxes_for_checkout(
        self, checkout_info, lines, previous_value
    ) -> Optional["TaxData"]:
        return trigger_all_webhooks_sync(
            WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            lambda: generate_checkout_payload_for_tax_calculation(
                checkout_info,
                lines,
            ),
            parse_tax_data,
            checkout_info.checkout,
            self.requestor,
            self.allow_replica,
        )

    def get_taxes_for_order(
        self, order: "Order", previous_value
    ) -> Optional["TaxData"]:
        return trigger_all_webhooks_sync(
            WebhookEventSyncType.ORDER_CALCULATE_TAXES,
            lambda: generate_order_payload_for_tax_calculation(order),
            parse_tax_data,
            order,
            self.requestor,
            self.allow_replica,
        )

    def get_shipping_methods_for_checkout(
        self, checkout: "Checkout", previous_value: Any
    ) -> List["ShippingMethodData"]:
        methods = []
        event_type = WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
        webhooks = get_webhooks_for_event(event_type)
        if webhooks:
            payload = generate_checkout_payload(checkout, self.requestor)
            cache_data = get_cache_data_for_shipping_list_methods_for_checkout(payload)
            for webhook in webhooks:
                response_data = trigger_webhook_sync_if_not_cached(
                    event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                    payload=payload,
                    webhook=webhook,
                    cache_data=cache_data,
                    subscribable_object=checkout,
                    request_timeout=WEBHOOK_SYNC_TIMEOUT,
                    cache_timeout=CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                )

                if response_data:
                    shipping_methods = parse_list_shipping_methods_response(
                        response_data, webhook.app
                    )
                    methods.extend(shipping_methods)
        return methods

    def get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType", "TaxClass"], previous_value: Any
    ):
        """Get tax code and description for a product or product type.

        If there is no active tax app, returns tax code from previous plugin.
        If there is no tax code defined for the product/product type,
        then return dummy values.
        """
        if not (tax_app := get_current_tax_app()):
            return previous_value

        meta_code_key = get_meta_code_key(tax_app)
        meta_description_key = get_meta_description_key(tax_app)

        default_tax_code = DEFAULT_TAX_CODE
        default_tax_description = DEFAULT_TAX_DESCRIPTION

        code = obj.get_value_from_metadata(meta_code_key, default_tax_code)
        description = obj.get_value_from_metadata(
            meta_description_key, default_tax_description
        )

        return TaxType(
            code=code,
            description=description,
        )

    def excluded_shipping_methods_for_order(
        self,
        order: "Order",
        available_shipping_methods: List["ShippingMethodData"],
        previous_value: List[ExcludedShippingMethod],
    ) -> List[ExcludedShippingMethod]:
        generate_function = generate_excluded_shipping_methods_for_order_payload
        payload_fun = lambda: generate_function(  # noqa: E731
            order,
            available_shipping_methods,
        )
        cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(order.id)
        return get_excluded_shipping_data(
            event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
            previous_value=previous_value,
            payload_fun=payload_fun,
            cache_key=cache_key,
            subscribable_object=order,
        )

    def excluded_shipping_methods_for_checkout(
        self,
        checkout: "Checkout",
        available_shipping_methods: List["ShippingMethodData"],
        previous_value: List[ExcludedShippingMethod],
    ) -> List[ExcludedShippingMethod]:
        generate_function = generate_excluded_shipping_methods_for_checkout_payload
        payload_function = lambda: generate_function(  # noqa: E731
            checkout,
            available_shipping_methods,
        )
        cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(checkout.token)
        return get_excluded_shipping_data(
            event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
            previous_value=previous_value,
            payload_fun=payload_function,
            cache_key=cache_key,
            subscribable_object=checkout,
        )

    def is_event_active(self, event: str, channel=Optional[str]):
        map_event = {
            "invoice_request": WebhookEventAsyncType.INVOICE_REQUESTED,
            "stored_payment_method_request_delete": (
                WebhookEventSyncType.STORED_PAYMENT_METHOD_DELETE_REQUESTED
            ),
            "payment_gateway_initialize_tokenization": (
                WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION
            ),
            "payment_method_initialize_tokenization": (
                WebhookEventSyncType.PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION
            ),
            "payment_method_process_tokenization": (
                WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION
            ),
        }

        if event in map_event:
            return any(get_webhooks_for_event(event_type=map_event[event]))
        return False
