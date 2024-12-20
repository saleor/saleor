import json
import logging
from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Final, Optional, Union

import graphene
from django.conf import settings

from ...app.models import App
from ...channel.models import Channel
from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ...checkout.models import Checkout
from ...core import EventDeliveryStatus
from ...core.models import EventDelivery
from ...core.notify import NotifyEventType
from ...core.taxes import TaxData, TaxType
from ...core.utils import build_absolute_uri
from ...core.utils.json_serializer import CustomJsonEncoder
from ...csv.notifications import get_default_export_payload
from ...graphql.core.context import SaleorContext
from ...graphql.webhook.subscription_payload import (
    generate_payload_promise_from_subscription,
    initialize_request,
)
from ...graphql.webhook.utils import (
    get_pregenerated_subscription_payload,
    get_subscription_query_hash,
)
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
from ...payment.utils import (
    create_failed_transaction_event,
    recalculate_refundable_for_checkout,
)
from ...settings import WEBHOOK_SYNC_TIMEOUT
from ...thumbnail.models import Thumbnail
from ...webhook.const import WEBHOOK_CACHE_DEFAULT_TIMEOUT
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
from ...webhook.transport.asynchronous.transport import (
    WebhookPayloadData,
    send_webhook_request_async,
    trigger_webhooks_async,
    trigger_webhooks_async_for_multiple_objects,
)
from ...webhook.transport.list_stored_payment_methods import (
    get_list_stored_payment_methods_data_dict,
    get_list_stored_payment_methods_from_response,
    get_response_for_payment_gateway_initialize_tokenization,
    get_response_for_payment_method_tokenization,
    get_response_for_stored_payment_method_request_delete,
    invalidate_cache_for_stored_payment_methods,
)
from ...webhook.transport.shipping import (
    get_cache_data_for_shipping_list_methods_for_checkout,
    get_excluded_shipping_data,
    parse_list_shipping_methods_response,
)
from ...webhook.transport.synchronous.transport import (
    trigger_all_webhooks_sync,
    trigger_transaction_request,
    trigger_webhook_sync,
    trigger_webhook_sync_if_not_cached,
)
from ...webhook.transport.utils import (
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
from ...webhook.utils import get_webhooks_for_event
from ..base_plugin import BasePlugin, ExcludedShippingMethod

if TYPE_CHECKING:
    from ...account.models import Address, Group, User
    from ...attribute.models import Attribute, AttributeValue
    from ...core.utils.translations import Translation
    from ...csv.models import ExportFile
    from ...discount.models import Promotion, PromotionRule, Voucher, VoucherCode
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
    from ...warehouse.models import Stock, Warehouse
    from ...webhook.models import Webhook


# Set the timeout for the shipping methods cache to 12 hours as it was the lowest
# time labels were valid for when checking documentation for the carriers
# (FedEx, UPS, TNT, DHL).
CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT: Final[int] = 3600 * 12


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
    def _get_webhooks_for_event(event_type, webhooks):
        if webhooks is not None:
            return webhooks
        return get_webhooks_for_event(event_type)

    @staticmethod
    def _serialize_payload(data):
        return json.dumps(data, cls=CustomJsonEncoder)

    def _generate_meta(self):
        return generate_meta(requestor_data=generate_requestor(self.requestor))

    def _trigger_metadata_updated_event(
        self, event_type, instance, webhooks=None, queue=None
    ):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            metadata_payload_generator = partial(
                generate_metadata_updated_payload, instance, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                instance,
                self.requestor,
                legacy_data_generator=metadata_payload_generator,
                queue=queue,
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

            self.trigger_webhooks_async(
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
            self.trigger_webhooks_async(
                self._serialize_payload(raw_payload),
                event_type,
                webhooks,
                data,
                self.requestor,
            )

    def trigger_webhooks_async(self, *args, **kwargs):
        return trigger_webhooks_async(*args, **kwargs, allow_replica=self.allow_replica)  # type: ignore[misc]

    def account_confirmed(self, user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_event(
            WebhookEventAsyncType.ACCOUNT_CONFIRMED,
            user,
        )
        return previous_value

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
        return previous_value

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
        return previous_value

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
        return previous_value

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
        return previous_value

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
        return previous_value

    def account_deleted(self, user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_account_event(
            WebhookEventAsyncType.ACCOUNT_DELETED,
            user,
        )
        return previous_value

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
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                address,
                self.requestor,
            )

    def address_created(self, address: "Address", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_address_event(WebhookEventAsyncType.ADDRESS_CREATED, address)
        return previous_value

    def address_updated(self, address: "Address", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_address_event(WebhookEventAsyncType.ADDRESS_UPDATED, address)
        return previous_value

    def address_deleted(self, address: "Address", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_address_event(WebhookEventAsyncType.ADDRESS_DELETED, address)
        return previous_value

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
            self.trigger_webhooks_async(
                payload, event_type, webhooks, app, self.requestor
            )

    def app_installed(self, app: "App", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_app_event(WebhookEventAsyncType.APP_INSTALLED, app)
        return previous_value

    def app_updated(self, app: "App", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_app_event(WebhookEventAsyncType.APP_UPDATED, app)
        return previous_value

    def app_deleted(self, app: "App", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_app_event(WebhookEventAsyncType.APP_DELETED, app)
        return previous_value

    def app_status_changed(self, app: "App", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_app_event(WebhookEventAsyncType.APP_STATUS_CHANGED, app)
        return previous_value

    def _trigger_attribute_event(self, event_type, attribute, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Attribute", attribute.id),
                    "name": attribute.name,
                    "slug": attribute.slug,
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                attribute,
                self.requestor,
            )

    def attribute_created(
        self, attribute: "Attribute", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_event(
            WebhookEventAsyncType.ATTRIBUTE_CREATED, attribute, webhooks=webhooks
        )
        return previous_value

    def attribute_updated(
        self, attribute: "Attribute", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_event(
            WebhookEventAsyncType.ATTRIBUTE_UPDATED, attribute, webhooks=webhooks
        )
        return previous_value

    def attribute_deleted(
        self, attribute: "Attribute", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_event(
            WebhookEventAsyncType.ATTRIBUTE_DELETED, attribute, webhooks=webhooks
        )
        return previous_value

    def _trigger_attribute_value_event(
        self, event_type, attribute_value, webhooks=None
    ):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
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
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                attribute_value,
                self.requestor,
            )

    def attribute_value_created(
        self, attribute_value: "AttributeValue", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_value_event(
            WebhookEventAsyncType.ATTRIBUTE_VALUE_CREATED,
            attribute_value,
            webhooks=webhooks,
        )
        return previous_value

    def attribute_value_updated(
        self, attribute_value: "AttributeValue", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_value_event(
            WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED, attribute_value
        )
        return previous_value

    def attribute_value_deleted(
        self, attribute_value: "AttributeValue", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_attribute_value_event(
            WebhookEventAsyncType.ATTRIBUTE_VALUE_DELETED,
            attribute_value,
            webhooks=webhooks,
        )
        return previous_value

    def __trigger_category_event(self, event_type, category, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Category", category.id),
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                category,
                self.requestor,
            )

    def category_created(self, category: "Category", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_category_event(WebhookEventAsyncType.CATEGORY_CREATED, category)
        return previous_value

    def category_updated(self, category: "Category", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_category_event(WebhookEventAsyncType.CATEGORY_UPDATED, category)
        return previous_value

    def category_deleted(
        self, category: "Category", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self.__trigger_category_event(
            WebhookEventAsyncType.CATEGORY_DELETED, category, webhooks=webhooks
        )
        return previous_value

    def __trigger_channel_event(self, event_type, channel, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Channel", channel.id),
                    "is_active": channel.is_active,
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                channel,
                self.requestor,
            )

    def channel_created(self, channel: "Channel", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(WebhookEventAsyncType.CHANNEL_CREATED, channel)
        return previous_value

    def channel_updated(
        self, channel: "Channel", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(
            WebhookEventAsyncType.CHANNEL_UPDATED, channel, webhooks=webhooks
        )
        return previous_value

    def channel_deleted(self, channel: "Channel", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(WebhookEventAsyncType.CHANNEL_DELETED, channel)
        return previous_value

    def channel_status_changed(self, channel: "Channel", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(
            WebhookEventAsyncType.CHANNEL_STATUS_CHANGED, channel
        )
        return previous_value

    def channel_metadata_updated(
        self, channel: "Channel", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self.__trigger_channel_event(
            WebhookEventAsyncType.CHANNEL_METADATA_UPDATED, channel
        )
        return previous_value

    def _trigger_gift_card_event(
        self, event_type, gift_card: "GiftCard", webhooks=None
    ):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
                    "is_active": gift_card.is_active,
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                gift_card,
                self.requestor,
            )

    def gift_card_created(
        self, gift_card: "GiftCard", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_gift_card_event(
            WebhookEventAsyncType.GIFT_CARD_CREATED, gift_card, webhooks=webhooks
        )
        return previous_value

    def gift_card_updated(self, gift_card: "GiftCard", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_gift_card_event(
            WebhookEventAsyncType.GIFT_CARD_UPDATED, gift_card
        )
        return previous_value

    def gift_card_deleted(
        self, gift_card: "GiftCard", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_gift_card_event(
            WebhookEventAsyncType.GIFT_CARD_DELETED, gift_card, webhooks=webhooks
        )
        return previous_value

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
            self.trigger_webhooks_async(
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
        return previous_value

    def gift_card_metadata_updated(
        self, gift_card: "GiftCard", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.GIFT_CARD_METADATA_UPDATED, gift_card
        )
        return previous_value

    def gift_card_status_changed(
        self, gift_card: "GiftCard", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_gift_card_event(
            WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED, gift_card, webhooks=webhooks
        )
        return previous_value

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
            self.trigger_webhooks_async(
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
        return previous_value

    def _get_webhooks_for_order_events(
        self,
        event_type: str,
        order: "Order",
        webhooks: Optional[Iterable["Webhook"]] = None,
    ) -> Iterable["Webhook"]:
        """Get webhooks for order events.

        Fetch all valid webhooks and filter out the ones that have a subscription query
        with filter that doesn't match to the order.
        """
        order_channel_slug = order.channel.slug
        if webhooks is None:
            webhooks = get_webhooks_for_event(event_type)
        filtered_webhooks = []
        for webhook in webhooks:
            if not webhook.subscription_query:
                filtered_webhooks.append(webhook)
                continue
            filterable_channel_slugs = list(webhook.filterable_channel_slugs)
            if not filterable_channel_slugs:
                filtered_webhooks.append(webhook)
                continue
            if order_channel_slug in filterable_channel_slugs:
                filtered_webhooks.append(webhook)
        return filtered_webhooks

    def order_created(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_CREATED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def _trigger_menu_event(self, event_type, menu, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Menu", menu.id),
                    "slug": menu.slug,
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload, event_type, webhooks, menu, self.requestor
            )

    def menu_created(self, menu: "Menu", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_menu_event(WebhookEventAsyncType.MENU_CREATED, menu)
        return previous_value

    def menu_updated(self, menu: "Menu", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_menu_event(WebhookEventAsyncType.MENU_UPDATED, menu)
        return previous_value

    def menu_deleted(self, menu: "Menu", previous_value: None, webhooks=None) -> None:
        if not self.active:
            return previous_value
        self._trigger_menu_event(
            WebhookEventAsyncType.MENU_DELETED, menu, webhooks=webhooks
        )
        return previous_value

    def __trigger_menu_item_event(self, event_type, menu_item, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
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
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                menu_item,
                self.requestor,
            )

    def menu_item_created(self, menu_item: "MenuItem", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_menu_item_event(
            WebhookEventAsyncType.MENU_ITEM_CREATED, menu_item
        )
        return previous_value

    def menu_item_updated(self, menu_item: "MenuItem", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self.__trigger_menu_item_event(
            WebhookEventAsyncType.MENU_ITEM_UPDATED, menu_item
        )
        return previous_value

    def menu_item_deleted(
        self, menu_item: "MenuItem", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self.__trigger_menu_item_event(
            WebhookEventAsyncType.MENU_ITEM_DELETED, menu_item, webhooks=webhooks
        )
        return previous_value

    def order_confirmed(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_CONFIRMED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def order_fully_paid(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_FULLY_PAID
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def order_paid(self, order: "Order", previous_value: None, webhooks=None) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_PAID
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def order_refunded(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_REFUNDED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def order_fully_refunded(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_FULLY_REFUNDED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def order_updated(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_UPDATED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def order_expired(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_EXPIRED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def sale_created(
        self,
        sale: "Promotion",
        current_catalogue: defaultdict[str, set[str]],
        previous_value: None,
    ) -> None:
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
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                sale,
                self.requestor,
                legacy_data_generator=sale_data_generator,
            )
        return previous_value

    def sale_updated(
        self,
        sale: "Promotion",
        previous_catalogue: defaultdict[str, set[str]],
        current_catalogue: defaultdict[str, set[str]],
        previous_value: None,
    ) -> None:
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
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                sale,
                self.requestor,
                legacy_data_generator=sale_data_generator,
            )
        return previous_value

    def sale_deleted(
        self,
        sale: "Promotion",
        previous_catalogue: defaultdict[str, set[str]],
        previous_value: None,
        webhooks=None,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.SALE_DELETED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            sale_data_generator = partial(
                generate_sale_payload,
                sale,
                previous_catalogue=previous_catalogue,
                requestor=self.requestor,
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                sale,
                self.requestor,
                legacy_data_generator=sale_data_generator,
            )
        return previous_value

    def sale_toggle(
        self,
        sale: "Promotion",
        catalogue: defaultdict[str, set[str]],
        previous_value: None,
        webhooks=None,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.SALE_TOGGLE
        if webhooks := get_webhooks_for_event(event_type, webhooks):
            sale_data_generator = partial(
                generate_sale_toggle_payload,
                sale,
                catalogue=catalogue,
                requestor=self.requestor,
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                sale,
                self.requestor,
                legacy_data_generator=sale_data_generator,
            )
        return previous_value

    def _trigger_promotion_event(
        self, event_type: str, promotion: "Promotion", webhooks=None
    ):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Promotion", promotion.id),
                }
            )
            self.trigger_webhooks_async(
                payload, event_type, webhooks, promotion, self.requestor
            )

    def promotion_created(
        self,
        promotion: "Promotion",
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_promotion_event(
            WebhookEventAsyncType.PROMOTION_CREATED, promotion
        )
        return previous_value

    def promotion_updated(
        self,
        promotion: "Promotion",
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_promotion_event(
            WebhookEventAsyncType.PROMOTION_UPDATED, promotion
        )
        return previous_value

    def promotion_deleted(
        self, promotion: "Promotion", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_promotion_event(
            WebhookEventAsyncType.PROMOTION_DELETED, promotion, webhooks=webhooks
        )
        return previous_value

    def promotion_started(
        self,
        promotion: "Promotion",
        previous_value: None,
        webhooks=None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_promotion_event(
            WebhookEventAsyncType.PROMOTION_STARTED, promotion, webhooks=webhooks
        )
        return previous_value

    def promotion_ended(
        self,
        promotion: "Promotion",
        previous_value: None,
        webhooks=None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_promotion_event(
            WebhookEventAsyncType.PROMOTION_ENDED, promotion, webhooks=webhooks
        )
        return previous_value

    def _trigger_promotion_rule_event(
        self, event_type: str, promotion_rule: "PromotionRule"
    ):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id(
                        "PromotionRule", promotion_rule.id
                    ),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                promotion_rule,
                self.requestor,
            )

    def promotion_rule_created(
        self,
        promotion_rule: "PromotionRule",
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_promotion_rule_event(
            WebhookEventAsyncType.PROMOTION_RULE_CREATED, promotion_rule
        )
        return previous_value

    def promotion_rule_updated(
        self,
        promotion_rule: "PromotionRule",
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_promotion_rule_event(
            WebhookEventAsyncType.PROMOTION_RULE_UPDATED, promotion_rule
        )
        return previous_value

    def promotion_rule_deleted(
        self,
        promotion_rule: "PromotionRule",
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_promotion_rule_event(
            WebhookEventAsyncType.PROMOTION_RULE_DELETED, promotion_rule
        )
        return previous_value

    def invoice_request(
        self,
        order: "Order",
        invoice: "Invoice",
        number: Optional[str],
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.INVOICE_REQUESTED
        if webhooks := get_webhooks_for_event(event_type):
            invoice_data_generator = partial(
                generate_invoice_payload, invoice, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                invoice,
                self.requestor,
                legacy_data_generator=invoice_data_generator,
            )
        return previous_value

    def invoice_delete(self, invoice: "Invoice", previous_value: None) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.INVOICE_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            invoice_data_generator = partial(
                generate_invoice_payload, invoice, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                invoice,
                self.requestor,
                legacy_data_generator=invoice_data_generator,
            )
        return previous_value

    def invoice_sent(
        self, invoice: "Invoice", email: str, previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.INVOICE_SENT
        if webhooks := get_webhooks_for_event(event_type):
            invoice_data_generator = partial(
                generate_invoice_payload, invoice, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                invoice,
                self.requestor,
                legacy_data_generator=invoice_data_generator,
            )
        return previous_value

    def order_cancelled(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_CANCELLED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def order_fulfilled(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_FULFILLED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def order_metadata_updated(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_METADATA_UPDATED
        webhooks = self._get_webhooks_for_order_events(event_type, order, webhooks)
        self._trigger_metadata_updated_event(
            event_type,
            order,
            webhooks=webhooks,
            queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        )
        return previous_value

    def _get_webhooks_for_order_bulk_created_event(
        self, order_channel_slugs: set[str]
    ) -> Iterable["Webhook"]:
        """Get webhooks for order events.

        Fetch all valid webhooks and filter out the ones that have a subscription query
        with filter that doesn't match to the order.
        """
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.ORDER_BULK_CREATED)
        filtered_webhooks = []
        for webhook in webhooks:
            if not webhook.subscription_query:
                filtered_webhooks.append(webhook)
                continue
            filterable_channel_slugs = list(webhook.filterable_channel_slugs)
            if not filterable_channel_slugs:
                filtered_webhooks.append(webhook)
                continue
            if order_channel_slugs.intersection(filterable_channel_slugs):
                filtered_webhooks.append(webhook)
        return filtered_webhooks

    def order_bulk_created(self, orders: list["Order"], previous_value: None) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.ORDER_BULK_CREATED
        channel_ids = {order.channel_id for order in orders}
        channel_slugs = Channel.objects.filter(id__in=channel_ids).values_list(
            "slug", flat=True
        )
        if webhooks := self._get_webhooks_for_order_bulk_created_event(
            set(channel_slugs)
        ):

            def generate_bulk_order_payload():
                return [
                    generate_order_payload(order, self.requestor) for order in orders
                ]

            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                orders,
                self.requestor,
                legacy_data_generator=generate_bulk_order_payload,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def draft_order_created(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.DRAFT_ORDER_CREATED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def draft_order_updated(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.DRAFT_ORDER_UPDATED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def draft_order_deleted(
        self, order: "Order", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.DRAFT_ORDER_DELETED
        if webhooks := self._get_webhooks_for_order_events(event_type, order, webhooks):
            order_data_generator = partial(
                generate_order_payload, order, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                order,
                self.requestor,
                legacy_data_generator=order_data_generator,
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def fulfillment_created(
        self,
        fulfillment: "Fulfillment",
        notify_customer: bool = True,
        previous_value: None = None,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.FULFILLMENT_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            fulfillment_data_generator = partial(
                generate_fulfillment_payload, fulfillment, self.requestor
            )
            self.trigger_webhooks_async(
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
        return previous_value

    def fulfillment_canceled(
        self, fulfillment: "Fulfillment", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.FULFILLMENT_CANCELED
        if webhooks := get_webhooks_for_event(event_type):
            fulfillment_data_generator = partial(
                generate_fulfillment_payload, fulfillment, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                fulfillment,
                self.requestor,
                legacy_data_generator=fulfillment_data_generator,
            )
        return previous_value

    def fulfillment_approved(
        self,
        fulfillment: "Fulfillment",
        notify_customer: Optional[bool] = True,
        previous_value: None = None,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.FULFILLMENT_APPROVED
        if webhooks := get_webhooks_for_event(event_type):
            fulfillment_data_generator = partial(
                generate_fulfillment_payload, fulfillment, self.requestor
            )
            self.trigger_webhooks_async(
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
        return previous_value

    def fulfillment_metadata_updated(
        self, fulfillment: "Fulfillment", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.FULFILLMENT_METADATA_UPDATED, fulfillment
        )
        return previous_value

    def tracking_number_updated(
        self, fulfillment: "Fulfillment", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.FULFILLMENT_TRACKING_NUMBER_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            fulfillment_data = generate_fulfillment_payload(fulfillment, self.requestor)
            self.trigger_webhooks_async(
                fulfillment_data,
                event_type,
                webhooks,
                fulfillment,
                self.requestor,
            )
        return previous_value

    def customer_created(self, customer: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CUSTOMER_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            customer_data_generator = partial(
                generate_customer_payload, customer, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                customer,
                self.requestor,
                legacy_data_generator=customer_data_generator,
            )
        return previous_value

    def customer_updated(
        self, customer: "User", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CUSTOMER_UPDATED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            customer_data_generator = partial(
                generate_customer_payload, customer, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                customer,
                self.requestor,
                legacy_data_generator=customer_data_generator,
            )
        return previous_value

    def customer_deleted(
        self, customer: "User", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CUSTOMER_DELETED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            customer_data_generator = partial(
                generate_customer_payload, customer, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                customer,
                self.requestor,
                legacy_data_generator=customer_data_generator,
            )
        return previous_value

    def customer_metadata_updated(
        self, customer: "User", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED, customer, webhooks=webhooks
        )
        return previous_value

    def collection_created(
        self, collection: "Collection", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.COLLECTION_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            collection_data_generator = partial(
                generate_collection_payload, collection, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                collection,
                self.requestor,
                legacy_data_generator=collection_data_generator,
            )
        return previous_value

    def collection_updated(
        self, collection: "Collection", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.COLLECTION_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            collection_data_generator = partial(
                generate_collection_payload, collection, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                collection,
                self.requestor,
                legacy_data_generator=collection_data_generator,
            )
        return previous_value

    def collection_deleted(
        self, collection: "Collection", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.COLLECTION_DELETED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            collection_data_generator = partial(
                generate_collection_payload, collection, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                collection,
                self.requestor,
                legacy_data_generator=collection_data_generator,
            )
        return previous_value

    def collection_metadata_updated(
        self, collection: "Collection", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.COLLECTION_METADATA_UPDATED, collection
        )
        return previous_value

    def product_created(
        self, product: "Product", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_CREATED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            product_data_generator = partial(
                generate_product_payload, product, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product,
                self.requestor,
                legacy_data_generator=product_data_generator,
            )
        return previous_value

    def product_updated(
        self, product: "Product", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_UPDATED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            product_data_generator = partial(
                generate_product_payload, product, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product,
                self.requestor,
                legacy_data_generator=product_data_generator,
            )
        return previous_value

    def product_metadata_updated(
        self, product: "Product", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value

        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.PRODUCT_METADATA_UPDATED, product
        )
        return previous_value

    def product_export_completed(
        self, export: "ExportFile", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_export_event(
            WebhookEventAsyncType.PRODUCT_EXPORT_COMPLETED,
            export,
        )
        return previous_value

    def product_deleted(
        self,
        product: "Product",
        variants: list[int],
        previous_value: None,
        webhooks=None,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_DELETED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            product_data_generator = partial(
                generate_product_deleted_payload, product, variants, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product,
                self.requestor,
                legacy_data_generator=product_data_generator,
            )
        return previous_value

    def product_media_created(
        self, media: "ProductMedia", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_MEDIA_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            media_data_generator = partial(generate_product_media_payload, media)
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                media,
                self.requestor,
                legacy_data_generator=media_data_generator,
            )
        return previous_value

    def product_media_updated(
        self, media: "ProductMedia", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_MEDIA_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            media_data_generator = partial(generate_product_media_payload, media)
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                media,
                self.requestor,
                legacy_data_generator=media_data_generator,
            )
        return previous_value

    def product_media_deleted(
        self, media: "ProductMedia", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_MEDIA_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            media_data_generator = partial(generate_product_media_payload, media)
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                media,
                self.requestor,
                legacy_data_generator=media_data_generator,
            )
        return previous_value

    def product_variant_created(
        self, product_variant: "ProductVariant", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_CREATED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            product_variant_data_generator = partial(
                generate_product_variant_payload, [product_variant], self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product_variant,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )
        return previous_value

    def product_variant_updated(
        self,
        product_variant: "ProductVariant",
        previous_value: None,
        webhooks=None,
        **kwargs,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            product_variant_data_generator = partial(
                generate_product_variant_payload, [product_variant], self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product_variant,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
                **kwargs,
            )
        return previous_value

    def product_variant_deleted(
        self, product_variant: "ProductVariant", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DELETED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            product_variant_data_generator = partial(
                generate_product_variant_payload, [product_variant], self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                product_variant,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )
        return previous_value

    def product_variant_metadata_updated(
        self, product_variant: "ProductVariant", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_METADATA_UPDATED, product_variant
        )
        return previous_value

    def product_variant_out_of_stock(
        self, stock: "Stock", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            product_variant_data_generator = partial(
                generate_product_variant_with_stock_payload, [stock]
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                stock,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )
        return previous_value

    def product_variant_back_in_stock(
        self, stock: "Stock", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            product_variant_data_generator = partial(
                generate_product_variant_with_stock_payload, [stock], self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                stock,
                self.requestor,
                legacy_data_generator=product_variant_data_generator,
            )
        return previous_value

    def product_variant_stocks_updated(
        self, stocks: list["Stock"], previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            webhook_payload_details = []
            for stock in stocks:
                product_variant_data_generator = partial(
                    generate_product_variant_with_stock_payload, [stock], self.requestor
                )
                webhook_payload_details.append(
                    WebhookPayloadData(
                        subscribable_object=stock,
                        legacy_data_generator=product_variant_data_generator,
                        data=None,
                    )
                )
            trigger_webhooks_async_for_multiple_objects(
                event_type,
                webhooks,
                webhook_payloads_data=webhook_payload_details,
                requestor=self.requestor,
            )
        return previous_value

    def checkout_created(
        self, checkout: "Checkout", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CHECKOUT_CREATED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            checkout_data_generator = partial(
                generate_checkout_payload, checkout, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                checkout,
                self.requestor,
                legacy_data_generator=checkout_data_generator,
                queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def checkout_updated(
        self, checkout: "Checkout", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            checkout_data_generator = partial(
                generate_checkout_payload, checkout, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                checkout,
                self.requestor,
                legacy_data_generator=checkout_data_generator,
                queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def checkout_fully_paid(
        self, checkout: "Checkout", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.CHECKOUT_FULLY_PAID
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            checkout_data_generator = partial(
                generate_checkout_payload, checkout, self.requestor
            )
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                checkout,
                self.requestor,
                legacy_data_generator=checkout_data_generator,
                queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            )
        return previous_value

    def checkout_metadata_updated(
        self, checkout: "Checkout", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED, checkout, webhooks=webhooks
        )
        return previous_value

    def notify(
        self,
        event: Union[NotifyEventType, str],
        payload_func: Callable,
        previous_value: None,
    ) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.NOTIFY_USER
        if webhooks := get_webhooks_for_event(event_type):
            payload = payload_func()
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
                logger.info(
                    "Webhook %s triggered for %s notify event.", event_type, event
                )
            self.trigger_webhooks_async(data, event_type, webhooks)
        return previous_value

    def page_created(self, page: "Page", previous_value: None) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PAGE_CREATED
        if webhooks := get_webhooks_for_event(event_type):
            page_data_generator = partial(generate_page_payload, page, self.requestor)
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                page,
                self.requestor,
                legacy_data_generator=page_data_generator,
            )
        return previous_value

    def page_updated(self, page: "Page", previous_value: None) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PAGE_UPDATED
        if webhooks := get_webhooks_for_event(event_type):
            page_data_generator = partial(generate_page_payload, page, self.requestor)
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                page,
                self.requestor,
                legacy_data_generator=page_data_generator,
            )
        return previous_value

    def page_deleted(self, page: "Page", previous_value: None) -> None:
        if not self.active:
            return previous_value
        event_type = WebhookEventAsyncType.PAGE_DELETED
        if webhooks := get_webhooks_for_event(event_type):
            page_data_generator = partial(generate_page_payload, page, self.requestor)
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                page,
                self.requestor,
                legacy_data_generator=page_data_generator,
            )
        return previous_value

    def _trigger_page_type_event(self, event_type, page_type, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("PageType", page_type.id),
                    "name": page_type.name,
                    "slug": page_type.slug,
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload, event_type, webhooks, page_type, self.requestor
            )

    def page_type_created(self, page_type: "PageType", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_page_type_event(
            WebhookEventAsyncType.PAGE_TYPE_CREATED, page_type
        )
        return previous_value

    def page_type_updated(self, page_type: "PageType", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_page_type_event(
            WebhookEventAsyncType.PAGE_TYPE_UPDATED, page_type
        )
        return previous_value

    def page_type_deleted(
        self, page_type: "PageType", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_page_type_event(
            WebhookEventAsyncType.PAGE_TYPE_DELETED, page_type, webhooks=webhooks
        )
        return previous_value

    def _trigger_permission_group_event(self, event_type, group) -> None:
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Group", group.id),
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload, event_type, webhooks, group, self.requestor
            )

    def permission_group_created(self, group: "Group", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_permission_group_event(
            WebhookEventAsyncType.PERMISSION_GROUP_CREATED, group
        )
        return previous_value

    def permission_group_updated(self, group: "Group", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_permission_group_event(
            WebhookEventAsyncType.PERMISSION_GROUP_UPDATED, group
        )
        return previous_value

    def permission_group_deleted(self, group: "Group", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_permission_group_event(
            WebhookEventAsyncType.PERMISSION_GROUP_DELETED, group
        )
        return previous_value

    def _trigger_shipping_price_event(self, event_type, shipping_method, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id(
                        "ShippingMethodType", shipping_method.id
                    ),
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                shipping_method,
                self.requestor,
            )

    def shipping_price_created(
        self, shipping_method: "ShippingMethod", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_price_event(
            WebhookEventAsyncType.SHIPPING_PRICE_CREATED, shipping_method
        )
        return previous_value

    def shipping_price_updated(
        self, shipping_method: "ShippingMethod", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_price_event(
            WebhookEventAsyncType.SHIPPING_PRICE_UPDATED, shipping_method
        )
        return previous_value

    def shipping_price_deleted(
        self, shipping_method: "ShippingMethod", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value

        self._trigger_shipping_price_event(
            WebhookEventAsyncType.SHIPPING_PRICE_DELETED,
            shipping_method,
            webhooks=webhooks,
        )
        return previous_value

    def _trigger_shipping_zone_event(self, event_type, shipping_zone, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("ShippingZone", shipping_zone.id),
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                shipping_zone,
                self.requestor,
            )

    def shipping_zone_created(
        self, shipping_zone: "ShippingZone", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_zone_event(
            WebhookEventAsyncType.SHIPPING_ZONE_CREATED, shipping_zone
        )
        return previous_value

    def shipping_zone_updated(
        self, shipping_zone: "ShippingZone", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_zone_event(
            WebhookEventAsyncType.SHIPPING_ZONE_UPDATED, shipping_zone
        )
        return previous_value

    def shipping_zone_deleted(
        self, shipping_zone: "ShippingZone", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_shipping_zone_event(
            WebhookEventAsyncType.SHIPPING_ZONE_DELETED,
            shipping_zone,
            webhooks=webhooks,
        )
        return previous_value

    def shipping_zone_metadata_updated(
        self, shipping_zone: "ShippingZone", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.SHIPPING_ZONE_METADATA_UPDATED, shipping_zone
        )
        return previous_value

    def _trigger_staff_event(self, event_type, staff_user, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("User", staff_user.id),
                    "email": staff_user.email,
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                staff_user,
                self.requestor,
            )

    def staff_created(self, staff_user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_staff_event(WebhookEventAsyncType.STAFF_CREATED, staff_user)
        return previous_value

    def staff_updated(self, staff_user: "User", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_staff_event(WebhookEventAsyncType.STAFF_UPDATED, staff_user)
        return previous_value

    def staff_deleted(
        self, staff_user: "User", previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_staff_event(
            WebhookEventAsyncType.STAFF_DELETED, staff_user, webhooks=webhooks
        )
        return previous_value

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
        return previous_value

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
            self.trigger_webhooks_async(
                None,
                event_type,
                webhooks,
                subscribable_object=thumbnail,
                legacy_data_generator=thumbnail_data_generator,
            )
        return previous_value

    def translations_created(
        self,
        translations: list["Translation"],
        previous_value: None,
        webhooks=None,
    ) -> None:
        return self._handle_translations(
            translations,
            previous_value,
            event_type=WebhookEventAsyncType.TRANSLATION_CREATED,
            webhooks=webhooks,
        )

    def translations_updated(
        self,
        translations: list["Translation"],
        previous_value: None,
        webhooks=None,
    ) -> None:
        return self._handle_translations(
            translations,
            previous_value,
            event_type=WebhookEventAsyncType.TRANSLATION_UPDATED,
            webhooks=webhooks,
        )

    def _handle_translations(
        self,
        translations: list["Translation"],
        previous_value: None,
        event_type: str,
        webhooks=None,
    ) -> None:
        if not self.active:
            return previous_value
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            webhook_payload_details = []
            for translation in translations:
                translation_data_generator = partial(
                    generate_translation_payload, translation, self.requestor
                )
                webhook_payload_details.append(
                    WebhookPayloadData(
                        subscribable_object=translation,
                        legacy_data_generator=translation_data_generator,
                        data=None,
                    )
                )
            trigger_webhooks_async_for_multiple_objects(
                event_type,
                webhooks,
                webhook_payloads_data=webhook_payload_details,
                requestor=self.requestor,
            )
        return previous_value

    def _trigger_warehouse_event(self, event_type, warehouse):
        if webhooks := get_webhooks_for_event(event_type):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Warehouse", warehouse.id),
                    "name": warehouse.name,
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                warehouse,
                self.requestor,
            )

    def warehouse_created(self, warehouse: "Warehouse", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_warehouse_event(
            WebhookEventAsyncType.WAREHOUSE_CREATED, warehouse
        )
        return previous_value

    def warehouse_updated(self, warehouse: "Warehouse", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_warehouse_event(
            WebhookEventAsyncType.WAREHOUSE_UPDATED, warehouse
        )
        return previous_value

    def warehouse_deleted(self, warehouse: "Warehouse", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_warehouse_event(
            WebhookEventAsyncType.WAREHOUSE_DELETED, warehouse
        )
        return previous_value

    def warehouse_metadata_updated(
        self, warehouse: "Warehouse", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.WAREHOUSE_METADATA_UPDATED, warehouse
        )
        return previous_value

    def _trigger_voucher_event(self, event_type, voucher, code, webhooks=None):
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            payload = self._serialize_payload(
                {
                    "id": graphene.Node.to_global_id("Voucher", voucher.id),
                    "name": voucher.name,
                    "code": code,
                    "meta": self._generate_meta(),
                }
            )
            self.trigger_webhooks_async(
                payload,
                event_type,
                webhooks,
                voucher,
                self.requestor,
            )

    def voucher_created(
        self, voucher: "Voucher", code: str, previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_voucher_event(
            WebhookEventAsyncType.VOUCHER_CREATED, voucher, code
        )
        return previous_value

    def voucher_updated(
        self, voucher: "Voucher", code: str, previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_voucher_event(
            WebhookEventAsyncType.VOUCHER_UPDATED, voucher, code
        )
        return previous_value

    def voucher_deleted(
        self, voucher: "Voucher", code: str, previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_voucher_event(
            WebhookEventAsyncType.VOUCHER_DELETED, voucher, code, webhooks=webhooks
        )
        return previous_value

    def _trigger_voucher_code_event(
        self, event_type, voucher_codes, webhooks=None
    ) -> None:
        if webhooks := self._get_webhooks_for_event(event_type, webhooks):
            data = [
                {
                    "id": graphene.Node.to_global_id("VoucherCode", voucher_code.id),
                    "code": voucher_code.code,
                }
                for voucher_code in voucher_codes
            ]
            payload = self._serialize_payload(data)
            trigger_webhooks_async(
                payload, event_type, webhooks, voucher_codes, self.requestor
            )

    def voucher_codes_created(
        self, voucher_codes: list["VoucherCode"], previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_voucher_code_event(
            WebhookEventAsyncType.VOUCHER_CODES_CREATED, voucher_codes, webhooks
        )
        return previous_value

    def voucher_codes_deleted(
        self, voucher_codes: list["VoucherCode"], previous_value: None, webhooks=None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_voucher_code_event(
            WebhookEventAsyncType.VOUCHER_CODES_DELETED, voucher_codes, webhooks
        )
        return previous_value

    def voucher_metadata_updated(
        self, voucher: "Voucher", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.VOUCHER_METADATA_UPDATED, voucher
        )
        return previous_value

    def voucher_code_export_completed(
        self, export: "ExportFile", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        self._trigger_export_event(
            WebhookEventAsyncType.VOUCHER_CODE_EXPORT_COMPLETED,
            export,
        )
        return previous_value

    def shop_metadata_updated(self, shop: "SiteSettings", previous_value: None) -> None:
        if not self.active:
            return previous_value
        self._trigger_metadata_updated_event(
            WebhookEventAsyncType.SHOP_METADATA_UPDATED, shop
        )
        return previous_value

    def event_delivery_retry(
        self, delivery: "EventDelivery", previous_value: None
    ) -> None:
        if not self.active:
            return previous_value
        delivery_update(delivery, status=EventDeliveryStatus.PENDING)
        send_webhook_request_async.delay(delivery.pk)
        return previous_value

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
            False,
            subscribable_object=StoredPaymentMethodRequestDeleteData(
                payment_method_id=app_data.name,
                user=request_delete_data.user,
                channel=request_delete_data.channel,
            ),
            timeout=WEBHOOK_SYNC_TIMEOUT,
            requestor=self.requestor,
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
                    payload_dict,
                    self.allow_replica,
                    subscribable_object=list_payment_method_data,
                    request_timeout=WEBHOOK_SYNC_TIMEOUT,
                    cache_timeout=WEBHOOK_CACHE_DEFAULT_TIMEOUT,
                    requestor=self.requestor,
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
            False,
            subscribable_object=request_data,
            timeout=WEBHOOK_SYNC_TIMEOUT,
            requestor=self.requestor,
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
    ) -> None:
        if not self.active:
            return

        if not transaction_data.transaction_app_owner:
            create_failed_transaction_event(
                transaction_data.event,
                cause="Transaction request skipped. Missing relation to PaymentApp.",
            )
            recalculate_refundable_for_checkout(
                transaction_data.transaction, transaction_data.event
            )
            logger.warning(
                "Transaction request skipped for %s. Missing relation to App.",
                transaction_data.transaction.psp_reference,
            )
            return

        if not transaction_data.event:
            logger.warning(
                "Transaction request skipped for %s. Missing relation to TransactionEvent.",
                transaction_data.transaction.psp_reference,
            )
            return

        trigger_transaction_request(transaction_data, event_type, self.requestor)

    def transaction_charge_requested(
        self, transaction_data: "TransactionActionData", previous_value: Any
    ) -> None:
        self._request_transaction_action(
            transaction_data,
            WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
        )
        return previous_value

    def transaction_refund_requested(
        self, transaction_data: "TransactionActionData", previous_value: Any
    ) -> None:
        self._request_transaction_action(
            transaction_data,
            WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        )
        return previous_value

    def transaction_cancelation_requested(
        self, transaction_data: "TransactionActionData", previous_value: Any
    ) -> None:
        self._request_transaction_action(
            transaction_data,
            WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED,
        )
        return previous_value

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
                apps = (
                    App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
                    .for_event_type(event_type)
                    .filter(
                        identifier=payment_app_data.app_identifier,
                        removed_at__isnull=True,
                    )
                )
            else:
                apps = (
                    App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
                    .for_event_type(event_type)
                    .filter(pk=payment_app_data.app_pk, removed_at__isnull=True)
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
                event_type,
                webhook_payload,
                webhook,
                False,
                subscribable_object=payment,
                requestor=self.requestor,
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
        pregenerated_subscription_payloads: Optional[dict] = None,
    ):
        if pregenerated_subscription_payloads is None:
            pregenerated_subscription_payloads = {}

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

        pregenerated_subscription_payload = get_pregenerated_subscription_payload(
            webhook, pregenerated_subscription_payloads
        )
        response_data = trigger_webhook_sync(
            event_type=WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION,
            payload=json.dumps(payload, cls=CustomJsonEncoder),
            webhook=webhook,
            allow_replica=False,
            subscribable_object=subscribable_object,
            request=request,
            requestor=self.requestor,
            pregenerated_subscription_payload=pregenerated_subscription_payload,
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

        event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
        response_gateway: dict[str, PaymentGatewayData] = {}
        apps_identifiers = None

        gateways = {}
        if payment_gateways:
            gateways = {gateway.app_identifier: gateway for gateway in payment_gateways}
            apps_identifiers = list(gateways.keys())

        webhooks = get_webhooks_for_event(event_type, apps_identifier=apps_identifiers)
        request = initialize_request(
            self.requestor, sync_event=True, event_type=event_type
        )

        pregenerated_subscription_payloads: dict[int, dict[str, dict[str, Any]]] = (
            defaultdict(lambda: defaultdict(dict))
        )

        promises = []
        for webhook in webhooks:
            if not webhook.subscription_query:
                continue

            query_hash = get_subscription_query_hash(webhook.subscription_query)
            app = webhook.app

            gateway = gateways.get(app.identifier)
            gateway_data = None
            if gateway:
                gateway_data = gateway.data

            subscribable_object = (source_object, gateway_data, amount)

            promise_payload = generate_payload_promise_from_subscription(
                event_type=event_type,
                subscribable_object=subscribable_object,
                subscription_query=webhook.subscription_query,
                request=request,
                app=app,
            )
            promises.append(promise_payload)

            def store_payload(
                payload,
                app_id=app.pk,
                query_hash=query_hash,
            ):
                if payload:
                    pregenerated_subscription_payloads[app_id][query_hash] = payload

            promise_payload.then(store_payload)

        for webhook in webhooks:
            self._payment_gateway_initialize_session_for_single_webhook(
                webhook=webhook,
                gateways=gateways,
                response_gateway=response_gateway,
                amount=amount,
                source_object=source_object,
                request=request,
                pregenerated_subscription_payloads=pregenerated_subscription_payloads,
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

        pregenerated_subscription_payload: dict[str, Any] = {}
        if webhook.subscription_query:
            app = webhook.app
            request = initialize_request(
                self.requestor, sync_event=True, event_type=webhook_event
            )
            promise_payload = generate_payload_promise_from_subscription(
                event_type=webhook_event,
                subscribable_object=transaction_session_data,
                subscription_query=webhook.subscription_query,
                request=request,
                app=app,
            )
            if promise_payload:
                pregenerated_subscription_payload = promise_payload.get() or {}

        response_data = trigger_webhook_sync(
            event_type=webhook_event,
            payload=payload,
            webhook=webhook,
            allow_replica=False,
            subscribable_object=transaction_session_data,
            requestor=self.requestor,
            pregenerated_subscription_payload=pregenerated_subscription_payload,
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
        checkout_lines: Optional[list["CheckoutLineInfo"]],
        previous_value,
        **kwargs,
    ) -> list["PaymentGateway"]:
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
                allow_replica=False,
                subscribable_object=checkout,
                requestor=self.requestor,
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
        return previous_value

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

    def __run_tax_webhook(
        self,
        event_type: str,
        app_identifier: str,
        payload_gen: Callable,
        subscriptable_object=None,
        pregenerated_subscription_payloads: Optional[dict] = None,
    ):
        if pregenerated_subscription_payloads is None:
            pregenerated_subscription_payloads = {}
        app = (
            App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .filter(
                identifier=app_identifier,
                is_active=True,
            )
            .order_by("-created_at")
            .first()
        )
        if app is None:
            logger.warning("Configured tax app doesn't exists.")
            return None
        webhook = get_webhooks_for_event(event_type, apps_ids=[app.id]).first()
        if webhook is None:
            logger.warning(
                "Configured tax app's webhook for checkout taxes doesn't exists."
            )
            return None

        request_context = initialize_request(
            self.requestor,
            event_type in WebhookEventSyncType.ALL,
            allow_replica=False,
            event_type=event_type,
        )

        pregenerated_subscription_payload = get_pregenerated_subscription_payload(
            webhook, pregenerated_subscription_payloads
        )
        response = trigger_webhook_sync(
            event_type=event_type,
            webhook=webhook,
            payload=payload_gen(),
            allow_replica=False,
            subscribable_object=subscriptable_object,
            request=request_context,
            requestor=self.requestor,
            pregenerated_subscription_payload=pregenerated_subscription_payload,
        )
        return parse_tax_data(response)

    def get_taxes_for_checkout(
        self,
        checkout_info,
        lines,
        app_identifier,
        previous_value,
        pregenerated_subscription_payloads: Optional[dict] = None,
    ) -> Optional["TaxData"]:
        if pregenerated_subscription_payloads is None:
            pregenerated_subscription_payloads = {}
        event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
        if app_identifier:
            return self.__run_tax_webhook(
                event_type,
                app_identifier,
                lambda: generate_checkout_payload_for_tax_calculation(
                    checkout_info, lines
                ),
                checkout_info.checkout,
                pregenerated_subscription_payloads=pregenerated_subscription_payloads,
            )
        return trigger_all_webhooks_sync(
            event_type,
            lambda: generate_checkout_payload_for_tax_calculation(
                checkout_info,
                lines,
            ),
            parse_tax_data,
            checkout_info.checkout,
            self.requestor,
            pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        )

    def get_taxes_for_order(
        self, order: "Order", app_identifier, previous_value
    ) -> Optional["TaxData"]:
        event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
        if app_identifier:
            return self.__run_tax_webhook(
                event_type,
                app_identifier,
                lambda: generate_order_payload_for_tax_calculation(order),
                order,
            )
        return trigger_all_webhooks_sync(
            WebhookEventSyncType.ORDER_CALCULATE_TAXES,
            lambda: generate_order_payload_for_tax_calculation(order),
            parse_tax_data,
            order,
            self.requestor,
        )

    def get_shipping_methods_for_checkout(
        self, checkout: "Checkout", previous_value: Any
    ) -> list["ShippingMethodData"]:
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
                    allow_replica=self.allow_replica,
                    subscribable_object=checkout,
                    request_timeout=WEBHOOK_SYNC_TIMEOUT,
                    cache_timeout=CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                    requestor=self.requestor,
                )

                if response_data:
                    shipping_methods = parse_list_shipping_methods_response(
                        response_data, webhook.app
                    )
                    methods.extend(shipping_methods)
        return methods

    def get_tax_code_from_object_meta(
        self,
        obj: Union["Product", "ProductType", "TaxClass"],
        previous_value: Any,
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
        available_shipping_methods: list["ShippingMethodData"],
        previous_value: list[ExcludedShippingMethod],
    ) -> list[ExcludedShippingMethod]:
        generate_function = generate_excluded_shipping_methods_for_order_payload
        payload_fun = lambda: generate_function(  # noqa: E731
            order,
            available_shipping_methods,
        )
        return get_excluded_shipping_data(
            event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
            previous_value=previous_value,
            payload_fun=payload_fun,
            subscribable_object=order,
            allow_replica=self.allow_replica,
            requestor=self.requestor,
        )

    def excluded_shipping_methods_for_checkout(
        self,
        checkout: "Checkout",
        available_shipping_methods: list["ShippingMethodData"],
        previous_value: list[ExcludedShippingMethod],
        pregenerated_subscription_payloads: Optional[dict] = None,
    ) -> list[ExcludedShippingMethod]:
        if pregenerated_subscription_payloads is None:
            pregenerated_subscription_payloads = {}
        generate_function = generate_excluded_shipping_methods_for_checkout_payload
        payload_function = lambda: generate_function(  # noqa: E731
            checkout,
            available_shipping_methods,
        )
        return get_excluded_shipping_data(
            event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
            previous_value=previous_value,
            payload_fun=payload_function,
            subscribable_object=checkout,
            allow_replica=self.allow_replica,
            pregenerated_subscription_payloads=pregenerated_subscription_payloads,
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
