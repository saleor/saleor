import graphene
from graphene import AbstractType, Union
from rx import Observable

from ... import __version__
from ...account.models import User
from ...attribute.models import AttributeTranslation, AttributeValueTranslation
from ...channel.models import Channel
from ...core.prices import quantize_price
from ...discount.models import (
    PromotionRuleTranslation,
    PromotionTranslation,
    VoucherTranslation,
)
from ...graphql.shop.types import Shop
from ...menu.models import MenuItemTranslation
from ...order.utils import get_all_shipping_methods_for_order
from ...page.models import PageTranslation
from ...payment.interface import (
    ListStoredPaymentMethodsRequestData,
    PaymentMethodInitializeTokenizationRequestData,
    PaymentMethodProcessTokenizationRequestData,
    PaymentMethodTokenizationBaseRequestData,
    StoredPaymentMethodRequestDeleteData,
    TransactionActionData,
    TransactionSessionData,
)
from ...product.models import (
    CategoryTranslation,
    CollectionTranslation,
    ProductTranslation,
    ProductVariantTranslation,
)
from ...shipping.models import ShippingMethodTranslation
from ...thumbnail.views import TYPE_TO_MODEL_DATA_MAPPING
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..account.types import User as UserType
from ..app.types import App as AppType
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.enums import TransactionFlowStrategyEnum
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..core.descriptions import (
    ADDED_IN_32,
    ADDED_IN_34,
    ADDED_IN_35,
    ADDED_IN_36,
    ADDED_IN_37,
    ADDED_IN_38,
    ADDED_IN_310,
    ADDED_IN_311,
    ADDED_IN_312,
    ADDED_IN_313,
    ADDED_IN_314,
    ADDED_IN_315,
    ADDED_IN_316,
    ADDED_IN_317,
    ADDED_IN_318,
    ADDED_IN_319,
    DEPRECATED_IN_3X_EVENT,
    PREVIEW_FEATURE,
)
from ..core.doc_category import (
    DOC_CATEGORY_CHECKOUT,
    DOC_CATEGORY_DISCOUNTS,
    DOC_CATEGORY_GIFT_CARDS,
    DOC_CATEGORY_MISC,
    DOC_CATEGORY_ORDERS,
    DOC_CATEGORY_PAYMENTS,
    DOC_CATEGORY_PRODUCTS,
    DOC_CATEGORY_SHIPPING,
    DOC_CATEGORY_TAXES,
    DOC_CATEGORY_USERS,
)
from ..core.scalars import JSON, DateTime, PositiveDecimal
from ..core.types import NonNullList, SubscriptionObjectType
from ..core.types.order_or_checkout import OrderOrCheckout
from ..order.dataloaders import OrderByIdLoader
from ..order.types import Order, OrderGrantedRefund
from ..payment.enums import TokenizedPaymentFlowEnum, TransactionActionEnum
from ..payment.types import TransactionItem
from ..plugins.dataloaders import plugin_manager_promise_callback
from ..product.dataloaders import ProductVariantByIdLoader
from ..shipping.dataloaders import ShippingMethodChannelListingByChannelSlugLoader
from ..shipping.types import ShippingMethod
from ..translations import types as translation_types
from ..warehouse.dataloaders import WarehouseByIdLoader
from .resolvers import resolve_shipping_methods_for_checkout

TRANSLATIONS_TYPES_MAP = {
    ProductTranslation: translation_types.ProductTranslation,
    CollectionTranslation: translation_types.CollectionTranslation,
    CategoryTranslation: translation_types.CategoryTranslation,
    AttributeTranslation: translation_types.AttributeTranslation,
    AttributeValueTranslation: translation_types.AttributeValueTranslation,
    ProductVariantTranslation: translation_types.ProductVariantTranslation,
    PageTranslation: translation_types.PageTranslation,
    ShippingMethodTranslation: translation_types.ShippingMethodTranslation,
    VoucherTranslation: translation_types.VoucherTranslation,
    MenuItemTranslation: translation_types.MenuItemTranslation,
    PromotionTranslation: translation_types.PromotionTranslation,
    PromotionRuleTranslation: translation_types.PromotionRuleTranslation,
}


class IssuingPrincipal(Union):
    class Meta:
        types = (AppType, UserType)

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        if isinstance(instance, User):
            return UserType
        return AppType


class Event(graphene.Interface):
    issued_at = DateTime(description="Time of the event.")
    version = graphene.String(description="Saleor version that triggered the event.")
    issuing_principal = graphene.Field(
        IssuingPrincipal,
        description="The user or application that triggered the event.",
    )
    recipient = graphene.Field(
        "saleor.graphql.app.types.App",
        description="The application receiving the webhook.",
    )

    @classmethod
    def get_type(cls, object_type: str):
        return WEBHOOK_TYPES_MAP.get(object_type)

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        type_str, _ = instance
        return cls.get_type(type_str)

    @staticmethod
    def resolve_issued_at(_root, info: ResolveInfo):
        return info.context.request_time

    @staticmethod
    def resolve_version(_root, _info: ResolveInfo):
        return __version__

    @staticmethod
    def resolve_recipient(_root, info: ResolveInfo):
        return info.context.app

    @staticmethod
    def resolve_issuing_principal(_root, info: ResolveInfo):
        if not info.context.requestor:
            return None
        return info.context.requestor


class AccountOperationBase(AbstractType):
    redirect_url = graphene.String(
        description="The URL to redirect the user after he accepts the request.",
        required=False,
    )
    user = graphene.Field(
        UserType,
        description="The user the event relates to.",
    )
    channel = graphene.Field(
        "saleor.graphql.channel.types.Channel",
        description="The channel data.",
    )
    token = graphene.String(description="The token required to confirm request.")
    shop = graphene.Field(Shop, description="Shop data.")

    @staticmethod
    def resolve_user(root, _info: ResolveInfo):
        _, data = root
        return data["user"]

    @staticmethod
    def resolve_redirect_url(root, _info: ResolveInfo):
        _, data = root
        return data.get("redirect_url")

    @staticmethod
    def resolve_channel(root, info: ResolveInfo):
        _, data = root
        return Channel.objects.using(get_database_connection_name(info.context)).get(
            slug=data["channel_slug"]
        )

    @staticmethod
    def resolve_token(root, _info: ResolveInfo):
        _, data = root
        return data["token"]

    @staticmethod
    def resolve_shop(root, _info: ResolveInfo):
        return Shop()


class AccountConfirmed(SubscriptionObjectType, AccountOperationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when account is confirmed." + ADDED_IN_315
        doc_category = DOC_CATEGORY_USERS


class AccountConfirmationRequested(SubscriptionObjectType, AccountOperationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when account confirmation requested. This event is always sent."
            " enableAccountConfirmationByEmail flag set to True is not required."
            + ADDED_IN_315
        )
        doc_category = DOC_CATEGORY_USERS


class AccountChangeEmailRequested(SubscriptionObjectType, AccountOperationBase):
    new_email = graphene.String(
        description="The new email address the user wants to change to.",
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when account change email is requested." + ADDED_IN_315
        )
        doc_category = DOC_CATEGORY_USERS

    @staticmethod
    def resolve_new_email(root, _info: ResolveInfo):
        _, data = root
        return data["new_email"]


class AccountEmailChanged(SubscriptionObjectType, AccountOperationBase):
    new_email = graphene.String(
        description="The new email address.",
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when account email is changed." + ADDED_IN_315
        doc_category = DOC_CATEGORY_USERS


class AccountSetPasswordRequested(SubscriptionObjectType, AccountOperationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when setting a new password is requested." + ADDED_IN_315
        )
        doc_category = DOC_CATEGORY_USERS


class AccountDeleteRequested(SubscriptionObjectType, AccountOperationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when account delete is requested." + ADDED_IN_315
        doc_category = DOC_CATEGORY_USERS


class AccountDeleted(SubscriptionObjectType, AccountOperationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when account is deleted." + ADDED_IN_315
        doc_category = DOC_CATEGORY_USERS


class AddressBase(AbstractType):
    address = graphene.Field(
        "saleor.graphql.account.types.Address",
        description="The address the event relates to.",
    )

    @staticmethod
    def resolve_address(root, _info: ResolveInfo):
        _, address = root
        return address


class AddressCreated(SubscriptionObjectType, AddressBase):
    class Meta:
        root_type = "Address"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new address is created." + ADDED_IN_35


class AddressUpdated(SubscriptionObjectType, AddressBase):
    class Meta:
        root_type = "Address"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when address is updated." + ADDED_IN_35


class AddressDeleted(SubscriptionObjectType, AddressBase):
    class Meta:
        root_type = "Address"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when address is deleted." + ADDED_IN_35


class AppBase(AbstractType):
    app = graphene.Field(
        "saleor.graphql.app.types.App",
        description="The application the event relates to.",
    )

    @staticmethod
    def resolve_app(root, _info: ResolveInfo):
        _, app = root
        return app


class AppInstalled(SubscriptionObjectType, AppBase):
    class Meta:
        root_type = "App"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new app is installed." + ADDED_IN_34


class AppUpdated(SubscriptionObjectType, AppBase):
    class Meta:
        root_type = "App"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when app is updated." + ADDED_IN_34


class AppDeleted(SubscriptionObjectType, AppBase):
    class Meta:
        root_type = "App"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when app is deleted." + ADDED_IN_34


class AppStatusChanged(SubscriptionObjectType, AppBase):
    class Meta:
        root_type = "App"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when app status has changed." + ADDED_IN_34


class AttributeBase(AbstractType):
    attribute = graphene.Field(
        "saleor.graphql.attribute.types.Attribute",
        description="The attribute the event relates to.",
    )

    @staticmethod
    def resolve_attribute(root, _info: ResolveInfo):
        _, attribute = root
        return attribute


class AttributeCreated(SubscriptionObjectType, AttributeBase):
    class Meta:
        root_type = "Attribute"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new attribute is created." + ADDED_IN_35


class AttributeUpdated(SubscriptionObjectType, AttributeBase):
    class Meta:
        root_type = "Attribute"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when attribute is updated." + ADDED_IN_35


class AttributeDeleted(SubscriptionObjectType, AttributeBase):
    class Meta:
        root_type = "Attribute"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when attribute is deleted." + ADDED_IN_35


class AttributeValueBase(AbstractType):
    attribute_value = graphene.Field(
        "saleor.graphql.attribute.types.AttributeValue",
        description="The attribute value the event relates to.",
    )

    @staticmethod
    def resolve_attribute_value(root, _info: ResolveInfo):
        _, attribute = root
        return attribute


class AttributeValueCreated(SubscriptionObjectType, AttributeValueBase):
    class Meta:
        root_type = "AttributeValue"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new attribute value is created." + ADDED_IN_35


class AttributeValueUpdated(SubscriptionObjectType, AttributeValueBase):
    class Meta:
        root_type = "AttributeValue"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when attribute value is updated." + ADDED_IN_35


class AttributeValueDeleted(SubscriptionObjectType, AttributeValueBase):
    class Meta:
        root_type = "AttributeValue"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when attribute value is deleted." + ADDED_IN_35


class CategoryBase(AbstractType):
    category = graphene.Field(
        "saleor.graphql.product.types.Category",
        description="The category the event relates to.",
    )

    @staticmethod
    def resolve_category(root, info: ResolveInfo):
        _, category = root
        return category


class CategoryCreated(SubscriptionObjectType, CategoryBase):
    class Meta:
        root_type = "Category"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new category is created." + ADDED_IN_32


class CategoryUpdated(SubscriptionObjectType, CategoryBase):
    class Meta:
        root_type = "Category"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when category is updated." + ADDED_IN_32


class CategoryDeleted(SubscriptionObjectType, CategoryBase):
    class Meta:
        root_type = "Category"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when category is deleted." + ADDED_IN_32


class ChannelBase(AbstractType):
    channel = graphene.Field(
        "saleor.graphql.channel.types.Channel",
        description="The channel the event relates to.",
    )

    @staticmethod
    def resolve_channel(root, info: ResolveInfo):
        _, channel = root
        return channel


class ChannelCreated(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new channel is created." + ADDED_IN_32


class ChannelUpdated(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when channel is updated." + ADDED_IN_32


class ChannelDeleted(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when channel is deleted." + ADDED_IN_32


class ChannelStatusChanged(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when channel status has changed." + ADDED_IN_32


class ChannelMetadataUpdated(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when channel metadata is updated." + ADDED_IN_315


class OrderBase(AbstractType):
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="The order the event relates to.",
    )

    @staticmethod
    def resolve_order(root, info: ResolveInfo):
        _, order = root
        return order


class OrderCreated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new order is created." + ADDED_IN_32


class OrderUpdated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when order is updated." + ADDED_IN_32


class OrderConfirmed(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when order is confirmed." + ADDED_IN_32


class OrderFullyPaid(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when order is fully paid." + ADDED_IN_32


class OrderPaid(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Payment has been made. The order may be partially or fully paid."
            + ADDED_IN_314
            + PREVIEW_FEATURE
        )


class OrderRefunded(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "The order received a refund. The order may be partially or fully refunded."
            + ADDED_IN_314
            + PREVIEW_FEATURE
        )


class OrderFullyRefunded(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "The order is fully refunded." + ADDED_IN_314 + PREVIEW_FEATURE


class OrderFulfilled(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when order is fulfilled." + ADDED_IN_32


class OrderCancelled(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when order is canceled." + ADDED_IN_32


class OrderExpired(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when order becomes expired." + ADDED_IN_313 + PREVIEW_FEATURE
        )


class OrderMetadataUpdated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when order metadata is updated." + ADDED_IN_38


class OrderBulkCreated(SubscriptionObjectType):
    orders = NonNullList(
        Order,
        description="The orders the event relates to.",
    )

    @staticmethod
    def resolve_orders(root, _info: ResolveInfo):
        _, orders = root
        return orders

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when orders are imported." + ADDED_IN_314 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_ORDERS


class DraftOrderCreated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new draft order is created." + ADDED_IN_32


class DraftOrderUpdated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when draft order is updated." + ADDED_IN_32


class DraftOrderDeleted(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when draft order is deleted." + ADDED_IN_32


class GiftCardBase(AbstractType):
    gift_card = graphene.Field(
        "saleor.graphql.giftcard.types.GiftCard",
        description="The gift card the event relates to.",
    )

    @staticmethod
    def resolve_gift_card(root, info: ResolveInfo):
        _, gift_card = root
        return gift_card


class GiftCardCreated(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new gift card is created." + ADDED_IN_32


class GiftCardUpdated(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when gift card is updated." + ADDED_IN_32


class GiftCardDeleted(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when gift card is deleted." + ADDED_IN_32


class GiftCardSent(SubscriptionObjectType, GiftCardBase):
    channel = graphene.String(
        description="Slug of a channel for which this gift card email was sent."
    )
    sent_to_email = graphene.String(
        description="E-mail address to which gift card was sent.",
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when gift card is e-mailed." + ADDED_IN_313 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_GIFT_CARDS

    @staticmethod
    def resolve_gift_card(root, info: ResolveInfo):
        _, data = root
        return data["gift_card"]

    @staticmethod
    def resolve_channel(root, info: ResolveInfo):
        _, data = root
        return data["channel_slug"]

    @staticmethod
    def resolve_sent_to_email(root, info: ResolveInfo):
        _, data = root
        return data["sent_to_email"]


class GiftCardStatusChanged(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when gift card status has changed." + ADDED_IN_32


class GiftCardMetadataUpdated(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when gift card metadata is updated." + ADDED_IN_38


class GiftCardExportCompleted(SubscriptionObjectType):
    export = graphene.Field(
        "saleor.graphql.csv.types.ExportFile",
        description="The export file for gift cards.",
    )

    class Meta:
        root_type = "ExportFile"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when gift card export is completed." + ADDED_IN_316
        doc_category = DOC_CATEGORY_GIFT_CARDS

    @staticmethod
    def resolve_export(root, info: ResolveInfo):
        _, export_file = root
        return export_file


class MenuBase(AbstractType):
    menu = graphene.Field(
        "saleor.graphql.menu.types.Menu",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The menu the event relates to.",
    )

    @staticmethod
    def resolve_menu(root, info: ResolveInfo, channel=None):
        _, menu = root
        return ChannelContext(node=menu, channel_slug=channel)


class MenuCreated(SubscriptionObjectType, MenuBase):
    class Meta:
        root_type = "Menu"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new menu is created." + ADDED_IN_34


class MenuUpdated(SubscriptionObjectType, MenuBase):
    class Meta:
        root_type = "Menu"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when menu is updated." + ADDED_IN_34


class MenuDeleted(SubscriptionObjectType, MenuBase):
    class Meta:
        root_type = "Menu"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when menu is deleted." + ADDED_IN_34


class MenuItemBase(AbstractType):
    menu_item = graphene.Field(
        "saleor.graphql.menu.types.MenuItem",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The menu item the event relates to.",
    )

    @staticmethod
    def resolve_menu_item(root, info: ResolveInfo, channel=None):
        _, menu_item = root
        return ChannelContext(node=menu_item, channel_slug=channel)


class MenuItemCreated(SubscriptionObjectType, MenuItemBase):
    class Meta:
        root_type = "MenuItem"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new menu item is created." + ADDED_IN_34


class MenuItemUpdated(SubscriptionObjectType, MenuItemBase):
    class Meta:
        root_type = "MenuItem"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when menu item is updated." + ADDED_IN_34


class MenuItemDeleted(SubscriptionObjectType, MenuItemBase):
    class Meta:
        root_type = "MenuItem"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when menu item is deleted." + ADDED_IN_34


class ProductBase(AbstractType):
    product = graphene.Field(
        "saleor.graphql.product.types.Product",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The product the event relates to.",
    )
    category = graphene.Field(
        "saleor.graphql.product.types.categories.Category",
        description="The category of the product.",
    )

    @staticmethod
    def resolve_product(root, info: ResolveInfo, channel=None):
        _, product = root
        return ChannelContext(node=product, channel_slug=channel)

    @staticmethod
    def resolve_category(root, _info: ResolveInfo):
        _, product = root
        return product.category


class ProductCreated(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new product is created." + ADDED_IN_32


class ProductUpdated(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product is updated." + ADDED_IN_32


class ProductDeleted(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product is deleted." + ADDED_IN_32


class ProductMetadataUpdated(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product metadata is updated." + ADDED_IN_38


class ProductMediaBase(AbstractType):
    product_media = graphene.Field(
        "saleor.graphql.product.types.ProductMedia",
        description="The product media the event relates to.",
    )

    @staticmethod
    def resolve_product_media(root, info: ResolveInfo):
        _, media = root
        return media


class ProductMediaCreated(SubscriptionObjectType, ProductMediaBase):
    class Meta:
        root_type = "ProductMedia"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new product media is created." + ADDED_IN_312


class ProductMediaUpdated(SubscriptionObjectType, ProductMediaBase):
    class Meta:
        root_type = "ProductMedia"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product media is updated." + ADDED_IN_312


class ProductMediaDeleted(SubscriptionObjectType, ProductMediaBase):
    class Meta:
        root_type = "ProductMedia"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product media is deleted." + ADDED_IN_312


class ProductVariantBase(AbstractType):
    product_variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The product variant the event relates to.",
    )

    @staticmethod
    def resolve_product_variant(root, _info: ResolveInfo, channel=None):
        _, variant = root
        return ChannelContext(node=variant, channel_slug=channel)


class ProductVariantCreated(SubscriptionObjectType, ProductVariantBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new product variant is created." + ADDED_IN_32


class ProductVariantUpdated(SubscriptionObjectType, ProductVariantBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product variant is updated." + ADDED_IN_32


class ProductVariantDeleted(SubscriptionObjectType, ProductVariantBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product variant is deleted." + ADDED_IN_32


class ProductVariantMetadataUpdated(SubscriptionObjectType, ProductVariantBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when product variant metadata is updated." + ADDED_IN_38
        )


class ProductVariantOutOfStock(SubscriptionObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        root_type = "Stock"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product variant is out of stock." + ADDED_IN_32

    @staticmethod
    def resolve_product_variant(root, info: ResolveInfo, channel=None):
        _, stock = root
        variant = stock.product_variant
        return ChannelContext(node=variant, channel_slug=channel)

    @staticmethod
    def resolve_warehouse(root, _info: ResolveInfo):
        _, stock = root
        return stock.warehouse


class ProductVariantBackInStock(SubscriptionObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        root_type = "Stock"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product variant is back in stock." + ADDED_IN_32

    @staticmethod
    def resolve_product_variant(root, _info: ResolveInfo, channel=None):
        _, stock = root
        variant = stock.product_variant
        return ChannelContext(node=variant, channel_slug=channel)

    @staticmethod
    def resolve_warehouse(root, _info):
        _, stock = root
        return stock.warehouse


class ProductVariantStockUpdated(SubscriptionObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when product variant stock is updated."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PRODUCTS

    @staticmethod
    def resolve_product_variant(root, info: ResolveInfo, channel=None):
        _, stock = root
        return (
            ProductVariantByIdLoader(info.context)
            .load(stock.product_variant.id)
            .then(lambda variant: ChannelContext(node=variant, channel_slug=None))
        )

    @staticmethod
    def resolve_warehouse(root, info: ResolveInfo):
        _, stock = root
        return WarehouseByIdLoader(info.context).load(stock.warehouse_id)


class ProductExportCompleted(SubscriptionObjectType):
    export = graphene.Field(
        "saleor.graphql.csv.types.ExportFile",
        description="The export file for products.",
    )

    class Meta:
        root_type = "ExportFile"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when product export is completed." + ADDED_IN_316
        doc_category = DOC_CATEGORY_PRODUCTS

    @staticmethod
    def resolve_export(root, info: ResolveInfo):
        _, export_file = root
        return export_file


class SaleBase(AbstractType):
    sale = graphene.Field(
        "saleor.graphql.discount.types.Sale",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The sale the event relates to.",
    )

    @staticmethod
    def resolve_sale(root, info: ResolveInfo, channel=None):
        _, sale = root
        return ChannelContext(node=sale, channel_slug=channel)


class SaleCreated(SubscriptionObjectType, SaleBase):
    class Meta:
        root_type = "Sale"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new sale is created."
            + ADDED_IN_32
            + DEPRECATED_IN_3X_EVENT
            + " Use `PromotionCreated` event instead."
        )


class SaleUpdated(SubscriptionObjectType, SaleBase):
    class Meta:
        root_type = "Sale"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when sale is updated."
            + ADDED_IN_32
            + DEPRECATED_IN_3X_EVENT
            + " Use `PromotionUpdated` event instead."
        )


class SaleDeleted(SubscriptionObjectType, SaleBase):
    class Meta:
        root_type = "Sale"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when sale is deleted."
            + ADDED_IN_32
            + DEPRECATED_IN_3X_EVENT
            + " Use `PromotionDeleted` event instead."
        )


class SaleToggle(SubscriptionObjectType, SaleBase):
    sale = graphene.Field(
        "saleor.graphql.discount.types.Sale",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The sale the event relates to." + ADDED_IN_35,
    )

    class Meta:
        root_type = "Sale"
        enable_dry_run = True
        description = (
            "The event informs about the start or end of the sale."
            + ADDED_IN_35
            + DEPRECATED_IN_3X_EVENT
            + " Use `PromotionStarted` and `PromotionEnded` events instead."
        )
        interfaces = (Event,)


class PromotionBase(AbstractType):
    promotion = graphene.Field(
        "saleor.graphql.discount.types.Promotion",
        description="The promotion the event relates to.",
    )

    @staticmethod
    def resolve_promotion(root, info: ResolveInfo, channel=None):
        _, promotion = root
        return promotion


class PromotionCreated(SubscriptionObjectType, PromotionBase):
    class Meta:
        root_type = "Promotion"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new promotion is created." + ADDED_IN_317 + PREVIEW_FEATURE
        )


class PromotionUpdated(SubscriptionObjectType, PromotionBase):
    class Meta:
        root_type = "Promotion"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when promotion is updated." + ADDED_IN_317 + PREVIEW_FEATURE
        )


class PromotionDeleted(SubscriptionObjectType, PromotionBase):
    class Meta:
        root_type = "Promotion"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when promotion is deleted." + ADDED_IN_317 + PREVIEW_FEATURE
        )


class PromotionStarted(SubscriptionObjectType, PromotionBase):
    class Meta:
        root_type = "Promotion"
        enable_dry_run = True
        description = (
            "The event informs about the start of the promotion."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = (Event,)


class PromotionEnded(SubscriptionObjectType, PromotionBase):
    class Meta:
        root_type = "Promotion"
        enable_dry_run = True
        description = (
            "The event informs about the end of the promotion."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )
        interfaces = (Event,)


class PromotionRuleBase(AbstractType):
    promotion_rule = graphene.Field(
        "saleor.graphql.discount.types.PromotionRule",
        description="The promotion rule the event relates to.",
    )

    @staticmethod
    def resolve_promotion_rule(root, _info: ResolveInfo):
        _, promotion_rule = root
        return promotion_rule


class PromotionRuleCreated(SubscriptionObjectType, PromotionRuleBase):
    class Meta:
        root_type = "PromotionRule"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new promotion rule is created."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )


class PromotionRuleUpdated(SubscriptionObjectType, PromotionRuleBase):
    class Meta:
        root_type = "PromotionRule"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new promotion rule is updated."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )


class PromotionRuleDeleted(SubscriptionObjectType, PromotionRuleBase):
    class Meta:
        root_type = "PromotionRule"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new promotion rule is deleted."
            + ADDED_IN_317
            + PREVIEW_FEATURE
        )


class InvoiceBase(AbstractType):
    invoice = graphene.Field(
        "saleor.graphql.invoice.types.Invoice",
        description="The invoice the event relates to.",
    )
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="Order related to the invoice." + ADDED_IN_310,
    )

    @staticmethod
    def resolve_invoice(root, _info: ResolveInfo):
        _, invoice = root
        return invoice

    @staticmethod
    def resolve_order(root, _info):
        _, invoice = root
        return OrderByIdLoader(_info.context).load(invoice.order_id)


class InvoiceRequested(SubscriptionObjectType, InvoiceBase):
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        required=True,
        description="Order related to the invoice." + ADDED_IN_310,
    )

    class Meta:
        root_type = "Invoice"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when invoice is requested." + ADDED_IN_32


class InvoiceDeleted(SubscriptionObjectType, InvoiceBase):
    class Meta:
        root_type = "Invoice"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when invoice is deleted." + ADDED_IN_32


class InvoiceSent(SubscriptionObjectType, InvoiceBase):
    class Meta:
        root_type = "Invoice"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when invoice is sent." + ADDED_IN_32


class FulfillmentBase(AbstractType):
    fulfillment = graphene.Field(
        "saleor.graphql.order.types.Fulfillment",
        description="The fulfillment the event relates to.",
    )
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="The order the fulfillment belongs to.",
    )

    @staticmethod
    def resolve_fulfillment(root, _info: ResolveInfo):
        _, fulfillment = root
        return fulfillment

    @staticmethod
    def resolve_order(root, info: ResolveInfo):
        _, fulfillment = root
        return fulfillment.order


class FulfillmentTrackingNumberUpdated(SubscriptionObjectType, FulfillmentBase):
    class Meta:
        root_type = "Fulfillment"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when the tracking number is updated." + ADDED_IN_316
        doc_category = DOC_CATEGORY_ORDERS


class FulfillmentCreated(SubscriptionObjectType, FulfillmentBase):
    notify_customer = graphene.Boolean(
        description=(
            "If true, the app should send a notification to the customer."
            + ADDED_IN_316
        ),
        required=True,
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when new fulfillment is created." + ADDED_IN_34
        doc_category = DOC_CATEGORY_ORDERS

    @staticmethod
    def resolve_fulfillment(root, info: ResolveInfo):
        _, data = root
        return data["fulfillment"]

    @staticmethod
    def resolve_order(root, info: ResolveInfo):
        _, data = root
        return data["fulfillment"].order

    @staticmethod
    def resolve_notify_customer(root, _info: ResolveInfo):
        _, data = root
        return data["notify_customer"]


class FulfillmentCanceled(SubscriptionObjectType, FulfillmentBase):
    class Meta:
        root_type = "Fulfillment"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when fulfillment is canceled." + ADDED_IN_34


class FulfillmentApproved(SubscriptionObjectType, FulfillmentBase):
    notify_customer = graphene.Boolean(
        description="If true, send a notification to the customer." + ADDED_IN_316,
        required=True,
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when fulfillment is approved." + ADDED_IN_37
        doc_category = DOC_CATEGORY_ORDERS

    @staticmethod
    def resolve_fulfillment(root, info: ResolveInfo):
        _, data = root
        return data["fulfillment"]

    @staticmethod
    def resolve_order(root, info: ResolveInfo):
        _, data = root
        return data["fulfillment"].order

    @staticmethod
    def resolve_notify_customer(root, _info: ResolveInfo):
        _, data = root
        return data["notify_customer"]


class FulfillmentMetadataUpdated(SubscriptionObjectType, FulfillmentBase):
    class Meta:
        root_type = "Fulfillment"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when fulfillment metadata is updated." + ADDED_IN_38


class UserBase(AbstractType):
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The user the event relates to.",
    )

    @staticmethod
    def resolve_user(root, _info: ResolveInfo):
        _, user = root
        return user


class CustomerCreated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new customer user is created." + ADDED_IN_32


class CustomerUpdated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when customer user is updated." + ADDED_IN_32


class CustomerMetadataUpdated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when customer user metadata is updated." + ADDED_IN_38


class CollectionBase(AbstractType):
    collection = graphene.Field(
        "saleor.graphql.product.types.collections.Collection",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The collection the event relates to.",
    )

    @staticmethod
    def resolve_collection(root, _info: ResolveInfo, channel=None):
        _, collection = root
        return ChannelContext(node=collection, channel_slug=channel)


class CollectionCreated(SubscriptionObjectType, CollectionBase):
    class Meta:
        root_type = "Collection"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new collection is created." + ADDED_IN_32


class CollectionUpdated(SubscriptionObjectType, CollectionBase):
    class Meta:
        root_type = "Collection"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when collection is updated." + ADDED_IN_32


class CollectionDeleted(SubscriptionObjectType, CollectionBase):
    class Meta:
        root_type = "Collection"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when collection is deleted." + ADDED_IN_32


class CollectionMetadataUpdated(SubscriptionObjectType, CollectionBase):
    class Meta:
        root_type = "Collection"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when collection metadata is updated." + ADDED_IN_38


class CheckoutBase(AbstractType):
    checkout = graphene.Field(
        "saleor.graphql.checkout.types.Checkout",
        description="The checkout the event relates to.",
    )

    @staticmethod
    def resolve_checkout(root, _info: ResolveInfo):
        _, checkout = root
        return checkout


class CheckoutCreated(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = "Checkout"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new checkout is created." + ADDED_IN_32


class CheckoutUpdated(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = "Checkout"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when checkout is updated." + ADDED_IN_32


class CheckoutFullyPaid(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = "Checkout"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when checkout is fully paid with transactions."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )


class CheckoutMetadataUpdated(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = "Checkout"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when checkout metadata is updated." + ADDED_IN_38


class PageBase(AbstractType):
    page = graphene.Field(
        "saleor.graphql.page.types.Page", description="The page the event relates to."
    )

    @staticmethod
    def resolve_page(root, _info: ResolveInfo):
        _, page = root
        return page


class PageCreated(SubscriptionObjectType, PageBase):
    class Meta:
        root_type = "Page"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new page is created." + ADDED_IN_32


class PageUpdated(SubscriptionObjectType, PageBase):
    class Meta:
        root_type = "Page"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when page is updated." + ADDED_IN_32


class PageDeleted(SubscriptionObjectType, PageBase):
    class Meta:
        root_type = "Page"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when page is deleted." + ADDED_IN_32


class PageTypeBase(AbstractType):
    page_type = graphene.Field(
        "saleor.graphql.page.types.PageType",
        description="The page type the event relates to.",
    )

    @staticmethod
    def resolve_page_type(root, _info: ResolveInfo):
        _, page_type = root
        return page_type


class PageTypeCreated(SubscriptionObjectType, PageTypeBase):
    class Meta:
        root_type = "PageType"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new page type is created." + ADDED_IN_35


class PageTypeUpdated(SubscriptionObjectType, PageTypeBase):
    class Meta:
        root_type = "PageType"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when page type is updated." + ADDED_IN_35


class PageTypeDeleted(SubscriptionObjectType, PageTypeBase):
    class Meta:
        root_type = "PageType"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when page type is deleted." + ADDED_IN_35


class PermissionGroupBase(AbstractType):
    permission_group = graphene.Field(
        "saleor.graphql.account.types.Group",
        description="The permission group the event relates to.",
    )

    @staticmethod
    def resolve_permission_group(root, _info: ResolveInfo):
        _, permission_group = root
        return permission_group


class PermissionGroupCreated(SubscriptionObjectType, PermissionGroupBase):
    class Meta:
        root_type = "Group"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new permission group is created." + ADDED_IN_36


class PermissionGroupUpdated(SubscriptionObjectType, PermissionGroupBase):
    class Meta:
        root_type = "Group"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when permission group is updated." + ADDED_IN_36


class PermissionGroupDeleted(SubscriptionObjectType, PermissionGroupBase):
    class Meta:
        root_type = "Group"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when permission group is deleted." + ADDED_IN_36


class ShippingPriceBase(AbstractType):
    shipping_method = graphene.Field(
        "saleor.graphql.shipping.types.ShippingMethodType",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The shipping method the event relates to.",
    )
    shipping_zone = graphene.Field(
        "saleor.graphql.shipping.types.ShippingZone",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The shipping zone the shipping method belongs to.",
    )

    @staticmethod
    def resolve_shipping_method(root, _info: ResolveInfo, channel=None):
        _, shipping_method = root
        return ChannelContext(node=shipping_method, channel_slug=channel)

    @staticmethod
    def resolve_shipping_zone(root, _info: ResolveInfo, channel=None):
        _, shipping_method = root
        return ChannelContext(node=shipping_method.shipping_zone, channel_slug=channel)


class ShippingPriceCreated(SubscriptionObjectType, ShippingPriceBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when new shipping price is created." + ADDED_IN_32
        doc_category = DOC_CATEGORY_SHIPPING


class ShippingPriceUpdated(SubscriptionObjectType, ShippingPriceBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when shipping price is updated." + ADDED_IN_32
        doc_category = DOC_CATEGORY_SHIPPING


class ShippingPriceDeleted(SubscriptionObjectType, ShippingPriceBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when shipping price is deleted." + ADDED_IN_32
        doc_category = DOC_CATEGORY_SHIPPING


class ShippingZoneBase(AbstractType):
    shipping_zone = graphene.Field(
        "saleor.graphql.shipping.types.ShippingZone",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The shipping zone the event relates to.",
    )

    @staticmethod
    def resolve_shipping_zone(root, _info: ResolveInfo, channel=None):
        _, shipping_zone = root
        return ChannelContext(node=shipping_zone, channel_slug=channel)


class ShippingZoneCreated(SubscriptionObjectType, ShippingZoneBase):
    class Meta:
        root_type = "ShippingZone"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new shipping zone is created." + ADDED_IN_32


class ShippingZoneUpdated(SubscriptionObjectType, ShippingZoneBase):
    class Meta:
        root_type = "ShippingZone"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when shipping zone is updated." + ADDED_IN_32


class ShippingZoneDeleted(SubscriptionObjectType, ShippingZoneBase):
    class Meta:
        root_type = "ShippingZone"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when shipping zone is deleted." + ADDED_IN_32


class ShippingZoneMetadataUpdated(SubscriptionObjectType, ShippingZoneBase):
    class Meta:
        root_type = "ShippingZone"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when shipping zone metadata is updated." + ADDED_IN_38


class StaffCreated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new staff user is created." + ADDED_IN_35


class StaffUpdated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when staff user is updated." + ADDED_IN_35


class StaffDeleted(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when staff user is deleted." + ADDED_IN_35


class StaffSetPasswordRequested(SubscriptionObjectType, AccountOperationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when setting a new password for staff is requested."
            + ADDED_IN_315
        )
        doc_category = DOC_CATEGORY_USERS


class TransactionAction(SubscriptionObjectType, AbstractType):
    action_type = graphene.Field(
        TransactionActionEnum,
        required=True,
        description="Determines the action type.",
    )
    amount = PositiveDecimal(
        description="Transaction request amount. Null when action type is VOID.",
    )
    currency = graphene.String(
        description="Currency code." + ADDED_IN_316,
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS

    @staticmethod
    def resolve_amount(root: TransactionActionData, _info: ResolveInfo):
        if root.action_value is not None:
            return quantize_price(root.action_value, root.transaction.currency)
        return None

    @staticmethod
    def resolve_currency(root: TransactionActionData, _info: ResolveInfo):
        return root.transaction.currency


class TransactionActionBase(AbstractType):
    transaction = graphene.Field(
        TransactionItem,
        description="Look up a transaction.",
    )
    action = graphene.Field(
        TransactionAction,
        required=True,
        description="Requested action data.",
    )

    @staticmethod
    def resolve_transaction(root, _info: ResolveInfo):
        _, transaction_action_data = root
        transaction_action_data: TransactionActionData
        return transaction_action_data.transaction

    @staticmethod
    def resolve_action(root, _info: ResolveInfo):
        _, transaction_action_data = root
        transaction_action_data: TransactionActionData
        return transaction_action_data


class TransactionChargeRequested(TransactionActionBase, SubscriptionObjectType):
    class Meta:
        interfaces = (Event,)
        root_type = None
        enable_dry_run = False
        description = (
            "Event sent when transaction charge is requested."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionRefundRequested(TransactionActionBase, SubscriptionObjectType):
    granted_refund = graphene.Field(
        OrderGrantedRefund,
        description="Granted refund related to refund request."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
    )

    class Meta:
        interfaces = (Event,)
        root_type = None
        enable_dry_run = False
        description = (
            "Event sent when transaction refund is requested."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @staticmethod
    def resolve_granted_refund(root, _info: ResolveInfo):
        _, transaction_action_data = root
        transaction_action_data: TransactionActionData
        return transaction_action_data.granted_refund


class TransactionCancelationRequested(TransactionActionBase, SubscriptionObjectType):
    class Meta:
        interfaces = (Event,)
        root_type = None
        enable_dry_run = False
        description = (
            "Event sent when transaction cancelation is requested."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentGatewayInitializeSession(SubscriptionObjectType):
    source_object = graphene.Field(
        OrderOrCheckout, description="Checkout or order", required=True
    )
    data = graphene.Field(
        JSON,
        description="Payment gateway data in JSON format, received from storefront.",
    )
    amount = graphene.Field(
        PositiveDecimal,
        description="Amount requested for initializing the payment gateway.",
    )

    class Meta:
        interfaces = (Event,)
        root_type = None
        enable_dry_run = False
        description = (
            "Event sent when user wants to initialize the payment gateway."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @staticmethod
    def resolve_source_object(root, _info: ResolveInfo):
        _, objects = root
        source_object, _, _ = objects
        return source_object

    @staticmethod
    def resolve_data(root, _info: ResolveInfo):
        _, objects = root
        _, data, _ = objects
        return data

    @staticmethod
    def resolve_amount(root, _info: ResolveInfo):
        _, objects = root
        _, _, amount = objects
        return amount


class TransactionProcessAction(SubscriptionObjectType, AbstractType):
    amount = PositiveDecimal(
        description="Transaction amount to process.", required=True
    )
    currency = graphene.String(description="Currency of the amount.", required=True)
    action_type = graphene.Field(TransactionFlowStrategyEnum, required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionSessionBase(SubscriptionObjectType, AbstractType):
    transaction = graphene.Field(
        TransactionItem, description="Look up a transaction.", required=True
    )
    source_object = graphene.Field(
        OrderOrCheckout, description="Checkout or order", required=True
    )
    data = graphene.Field(
        JSON,
        description="Payment gateway data in JSON format, received from storefront.",
    )
    merchant_reference = graphene.String(
        description="Merchant reference assigned to this payment.", required=True
    )
    customer_ip_address = graphene.String(
        description=(
            "The customer's IP address. If not provided as a parameter in the "
            "mutation, Saleor will try to determine the customer's IP address on its "
            "own." + ADDED_IN_316
        ),
    )
    action = graphene.Field(
        TransactionProcessAction,
        description="Action to proceed for the transaction",
        required=True,
    )

    class Meta:
        abstract = True

    @classmethod
    def resolve_transaction(
        cls, root: tuple[str, TransactionSessionData], _info: ResolveInfo
    ):
        _, transaction_session_data = root
        return transaction_session_data.transaction

    @classmethod
    def resolve_source_object(
        cls, root: tuple[str, TransactionSessionData], _info: ResolveInfo
    ):
        _, transaction_session_data = root
        return transaction_session_data.source_object

    @classmethod
    def resolve_data(cls, root: tuple[str, TransactionSessionData], _info: ResolveInfo):
        _, transaction_session_data = root
        return transaction_session_data.payment_gateway_data.data

    @classmethod
    def resolve_merchant_reference(
        cls, root: tuple[str, TransactionSessionData], _info: ResolveInfo
    ):
        transaction = cls.resolve_transaction(root, _info)
        return graphene.Node.to_global_id("TransactionItem", transaction.token)

    @classmethod
    def resolve_action(
        cls, root: tuple[str, TransactionSessionData], _info: ResolveInfo
    ):
        _, transaction_session_data = root
        return transaction_session_data.action

    @classmethod
    def resolve_customer_ip_address(
        cls, root: tuple[str, TransactionSessionData], _info: ResolveInfo
    ):
        _, transaction_session_data = root
        return transaction_session_data.customer_ip_address


class TransactionInitializeSession(TransactionSessionBase):
    idempotency_key = graphene.String(
        description=(
            "Idempotency key assigned to the transaction initialize." + ADDED_IN_314
        ),
        required=True,
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when user starts processing the payment."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @classmethod
    def resolve_idempotency_key(
        cls, root: tuple[str, TransactionSessionData], _info: ResolveInfo
    ):
        _, transaction_session_data = root
        return transaction_session_data.idempotency_key


class TransactionProcessSession(TransactionSessionBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when user has additional payment action to process."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS


class ListStoredPaymentMethods(SubscriptionObjectType):
    user = graphene.Field(
        UserType,
        description=(
            "The user for which the app should return a list of payment methods."
        ),
        required=True,
    )
    channel = graphene.Field(
        "saleor.graphql.channel.types.Channel",
        description=(
            "Channel in context which was used to fetch the list of payment methods."
        ),
        required=True,
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "List payment methods stored for the user by payment gateway."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @classmethod
    def resolve_user(
        cls, root: tuple[str, ListStoredPaymentMethodsRequestData], _info: ResolveInfo
    ):
        _, payment_method_data = root
        return payment_method_data.user

    @classmethod
    def resolve_channel(
        cls, root: tuple[str, ListStoredPaymentMethodsRequestData], _info: ResolveInfo
    ):
        _, payment_method_data = root
        return payment_method_data.channel


class TransactionItemMetadataUpdated(SubscriptionObjectType):
    transaction = graphene.Field(
        TransactionItem,
        description="Look up a transaction.",
    )

    class Meta:
        root_type = "TransactionItem"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when transaction item metadata is updated." + ADDED_IN_38
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @staticmethod
    def resolve_transaction(root, _info: ResolveInfo):
        _, transaction_item = root
        return transaction_item


class StoredPaymentMethodDeleteRequested(SubscriptionObjectType):
    user = graphene.Field(
        UserType,
        description=(
            "The user for which the app should proceed with payment method delete "
            "request."
        ),
        required=True,
    )
    payment_method_id = graphene.Field(
        graphene.String,
        description=(
            "The ID of the payment method that should be deleted by the payment "
            "gateway."
        ),
        required=True,
    )

    channel = graphene.Field(
        "saleor.graphql.channel.types.Channel",
        description="Channel related to the requested delete action.",
        required=True,
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when user requests to delete a payment method."
            + ADDED_IN_316
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @classmethod
    def resolve_user(
        cls, root: tuple[str, StoredPaymentMethodRequestDeleteData], _info: ResolveInfo
    ):
        _, payment_method_data = root
        return payment_method_data.user

    @classmethod
    def resolve_payment_method_id(
        cls, root: tuple[str, StoredPaymentMethodRequestDeleteData], _info: ResolveInfo
    ):
        _, payment_method_data = root
        return payment_method_data.payment_method_id

    @classmethod
    def resolve_channel(
        cls, root: tuple[str, StoredPaymentMethodRequestDeleteData], _info: ResolveInfo
    ):
        _, payment_method_data = root
        return payment_method_data.channel


class PaymentMethodTokenizationBase(AbstractType):
    user = graphene.Field(
        UserType,
        description="The user related to the requested action.",
        required=True,
    )
    channel = graphene.Field(
        "saleor.graphql.channel.types.Channel",
        description="Channel related to the requested action.",
        required=True,
    )
    data = graphene.Field(
        JSON,
        description="Payment gateway data in JSON format, received from storefront.",
    )

    @classmethod
    def resolve_channel(
        cls,
        root: tuple[str, PaymentMethodTokenizationBaseRequestData],
        _info: ResolveInfo,
    ):
        _, payment_method_data = root
        return payment_method_data.channel

    @classmethod
    def resolve_user(
        cls,
        root: tuple[str, PaymentMethodTokenizationBaseRequestData],
        _info: ResolveInfo,
    ):
        _, payment_method_data = root
        return payment_method_data.user

    @classmethod
    def resolve_data(
        cls,
        root: tuple[str, PaymentMethodTokenizationBaseRequestData],
        _info: ResolveInfo,
    ):
        _, payment_method_data = root
        return payment_method_data.data


class PaymentGatewayInitializeTokenizationSession(
    SubscriptionObjectType, PaymentMethodTokenizationBase
):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent to initialize a new session in payment gateway to store the "
            "payment method. " + ADDED_IN_316 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentMethodInitializeTokenizationSession(
    SubscriptionObjectType, PaymentMethodTokenizationBase
):
    payment_flow_to_support = TokenizedPaymentFlowEnum(
        description=(
            "The payment flow that the tokenized payment method should support."
        ),
        required=True,
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when user requests a tokenization of payment method."
            + ADDED_IN_316
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @classmethod
    def resolve_payment_flow_to_support(
        cls,
        root: tuple[str, PaymentMethodInitializeTokenizationRequestData],
        _info: ResolveInfo,
    ):
        _, payment_method_data = root
        return payment_method_data.payment_flow_to_support


class PaymentMethodProcessTokenizationSession(
    SubscriptionObjectType, PaymentMethodTokenizationBase
):
    id = graphene.String(
        description=(
            "The ID returned by app from "
            "`PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION` webhook."
        ),
        required=True,
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when user continues a tokenization of payment method."
            + ADDED_IN_316
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @classmethod
    def resolve_id(
        cls,
        root: tuple[str, PaymentMethodProcessTokenizationRequestData],
        _info: ResolveInfo,
    ):
        _, payment_method_data = root
        return payment_method_data.id


class TranslationTypes(Union):
    class Meta:
        types = tuple(TRANSLATIONS_TYPES_MAP.values()) + (
            translation_types.SaleTranslation,
        )

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        instance_type = type(instance)
        if instance_type == PromotionTranslation and instance.promotion.old_sale_id:
            return translation_types.SaleTranslation
        if instance_type in TRANSLATIONS_TYPES_MAP:
            return TRANSLATIONS_TYPES_MAP[instance_type]

        return super().resolve_type(instance, info)


class TranslationBase(AbstractType):
    translation = graphene.Field(
        TranslationTypes, description="The translation the event relates to."
    )

    @staticmethod
    def resolve_translation(root, _info: ResolveInfo):
        _, translation = root
        return translation


class TranslationCreated(SubscriptionObjectType, TranslationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when new translation is created." + ADDED_IN_32
        doc_category = DOC_CATEGORY_MISC


class TranslationUpdated(SubscriptionObjectType, TranslationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when translation is updated." + ADDED_IN_32
        doc_category = DOC_CATEGORY_MISC


class VoucherBase(AbstractType):
    voucher = graphene.Field(
        "saleor.graphql.discount.types.Voucher",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The voucher the event relates to.",
    )

    @staticmethod
    def resolve_voucher(root, _info: ResolveInfo):
        _, voucher = root
        return ChannelContext(node=voucher, channel_slug=None)


class VoucherCreated(SubscriptionObjectType, VoucherBase):
    class Meta:
        root_type = "Voucher"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new voucher is created." + ADDED_IN_34


class VoucherUpdated(SubscriptionObjectType, VoucherBase):
    class Meta:
        root_type = "Voucher"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when voucher is updated." + ADDED_IN_34


class VoucherDeleted(SubscriptionObjectType, VoucherBase):
    class Meta:
        root_type = "Voucher"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when voucher is deleted." + ADDED_IN_34


class VoucherCodeBase(AbstractType):
    voucher_codes = NonNullList(
        "saleor.graphql.discount.types.VoucherCode",
        description="The voucher codes the event relates to.",
    )

    @staticmethod
    def resolve_voucher_codes(root, _info: ResolveInfo):
        _, voucher_codes = root
        return voucher_codes


class VoucherCodesCreated(SubscriptionObjectType, VoucherCodeBase):
    class Meta:
        root_type = "VoucherCode"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new voucher codes were created." + ADDED_IN_319


class VoucherCodesDeleted(SubscriptionObjectType, VoucherCodeBase):
    class Meta:
        root_type = "VoucherCode"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when voucher codes were deleted." + ADDED_IN_319


class VoucherMetadataUpdated(SubscriptionObjectType, VoucherBase):
    class Meta:
        root_type = "Voucher"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when voucher metadata is updated." + ADDED_IN_38


class VoucherCodeExportCompleted(SubscriptionObjectType):
    export = graphene.Field(
        "saleor.graphql.csv.types.ExportFile",
        description="The export file for voucher codes.",
    )

    class Meta:
        root_type = "ExportFile"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when voucher code export is completed." + ADDED_IN_318
        doc_category = DOC_CATEGORY_DISCOUNTS

    @staticmethod
    def resolve_export(root, _info: ResolveInfo):
        _, export_file = root
        return export_file


class ShopMetadataUpdated(SubscriptionObjectType, AbstractType):
    shop = graphene.Field(Shop, description="Shop data.")

    class Meta:
        root_type = "Shop"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when shop metadata is updated." + ADDED_IN_315

    @staticmethod
    def resolve_shop(root, _info: ResolveInfo):
        return Shop()


class PaymentBase(AbstractType):
    payment = graphene.Field(
        "saleor.graphql.payment.types.Payment",
        description="Look up a payment.",
    )

    @staticmethod
    def resolve_payment(root, _info: ResolveInfo):
        _, payment = root
        return payment


class PaymentAuthorize(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Authorize payment." + ADDED_IN_36
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentCaptureEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Capture payment." + ADDED_IN_36
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentRefundEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Refund payment." + ADDED_IN_36
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentVoidEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Void payment." + ADDED_IN_36
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentConfirmEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Confirm payment." + ADDED_IN_36
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentProcessEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Process payment." + ADDED_IN_36
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentListGateways(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "List payment gateways." + ADDED_IN_36
        doc_category = DOC_CATEGORY_PAYMENTS


class ShippingListMethodsForCheckout(SubscriptionObjectType, CheckoutBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36,
    )

    @staticmethod
    @plugin_manager_promise_callback
    def resolve_shipping_methods(root, info: ResolveInfo, manager):
        _, checkout = root
        database_connection_name = get_database_connection_name(info.context)
        return resolve_shipping_methods_for_checkout(
            info, checkout, manager, database_connection_name
        )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "List shipping methods for checkout." + ADDED_IN_36
        doc_category = DOC_CATEGORY_CHECKOUT


class CalculateTaxes(SubscriptionObjectType):
    tax_base = graphene.Field(
        "saleor.graphql.core.types.taxes.TaxableObject", required=True
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Synchronous webhook for calculating checkout/order taxes." + ADDED_IN_37
        )
        doc_category = DOC_CATEGORY_TAXES

    @staticmethod
    def resolve_tax_base(root, _info: ResolveInfo):
        _, tax_base = root
        return tax_base


class CheckoutFilterShippingMethods(SubscriptionObjectType, CheckoutBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36,
    )

    @staticmethod
    @plugin_manager_promise_callback
    def resolve_shipping_methods(root, info: ResolveInfo, manager):
        _, checkout = root
        database_connection_name = get_database_connection_name(info.context)
        return resolve_shipping_methods_for_checkout(
            info, checkout, manager, database_connection_name
        )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Filter shipping methods for checkout." + ADDED_IN_36
        doc_category = DOC_CATEGORY_CHECKOUT


class OrderFilterShippingMethods(SubscriptionObjectType, OrderBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36,
    )

    @staticmethod
    def resolve_shipping_methods(root, info: ResolveInfo):
        _, order = root

        def with_channel(channel):
            def with_listings(channel_listings):
                return get_all_shipping_methods_for_order(order, channel_listings)

            return (
                ShippingMethodChannelListingByChannelSlugLoader(info.context)
                .load(channel.slug)
                .then(with_listings)
            )

        return ChannelByIdLoader(info.context).load(order.channel_id).then(with_channel)

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Filter shipping methods for order." + ADDED_IN_36
        doc_category = DOC_CATEGORY_ORDERS


class WarehouseBase(AbstractType):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse",
        description="The warehouse the event relates to.",
    )

    @staticmethod
    def resolve_warehouse(root, _info: ResolveInfo):
        _, warehouse = root
        return warehouse


class WarehouseCreated(SubscriptionObjectType, WarehouseBase):
    class Meta:
        root_type = "Warehouse"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when new warehouse is created." + ADDED_IN_34


class WarehouseUpdated(SubscriptionObjectType, WarehouseBase):
    class Meta:
        root_type = "Warehouse"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when warehouse is updated." + ADDED_IN_34


class WarehouseDeleted(SubscriptionObjectType, WarehouseBase):
    class Meta:
        root_type = "Warehouse"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when warehouse is deleted." + ADDED_IN_34


class WarehouseMetadataUpdated(SubscriptionObjectType, WarehouseBase):
    class Meta:
        root_type = "Warehouse"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when warehouse metadata is updated." + ADDED_IN_38


class Subscription(SubscriptionObjectType):
    event = graphene.Field(
        Event,
        description="Look up subscription event." + ADDED_IN_32,
    )

    class Meta:
        doc_category = DOC_CATEGORY_MISC

    @staticmethod
    def resolve_event(root, info: ResolveInfo):
        return Observable.from_([root])


class ThumbnailCreated(SubscriptionObjectType):
    id = graphene.ID(description="Thumbnail id." + ADDED_IN_312)
    url = graphene.String(description="Thumbnail url." + ADDED_IN_312)
    object_id = graphene.ID(
        description="Object the thumbnail refers to." + ADDED_IN_312
    )
    media_url = graphene.String(description="Original media url." + ADDED_IN_312)

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Event sent when thumbnail is created." + ADDED_IN_312
        doc_category = DOC_CATEGORY_MISC

    @staticmethod
    def resolve_id(root, info: ResolveInfo):
        _, thumbnail = root
        return graphene.Node.to_global_id("Thumbnail", thumbnail.id)

    @staticmethod
    def resolve_url(root, info: ResolveInfo):
        _, thumbnail = root
        return thumbnail.image.url

    @staticmethod
    def resolve_object_id(root, info: ResolveInfo):
        _, thumbnail = root
        type = thumbnail.instance.__class__.__name__
        return graphene.Node.to_global_id(type, thumbnail.instance.id)

    @staticmethod
    def resolve_media_url(root, info: ResolveInfo):
        _, thumbnail = root
        type = thumbnail.instance.__class__.__name__
        image_field = TYPE_TO_MODEL_DATA_MAPPING[type].image_field
        image = getattr(thumbnail.instance, image_field, None)
        return image.url if image else None


SYNC_WEBHOOK_TYPES_MAP = {
    WebhookEventSyncType.PAYMENT_AUTHORIZE: PaymentAuthorize,
    WebhookEventSyncType.PAYMENT_CAPTURE: PaymentCaptureEvent,
    WebhookEventSyncType.PAYMENT_REFUND: PaymentRefundEvent,
    WebhookEventSyncType.PAYMENT_VOID: PaymentVoidEvent,
    WebhookEventSyncType.PAYMENT_CONFIRM: PaymentConfirmEvent,
    WebhookEventSyncType.PAYMENT_PROCESS: PaymentProcessEvent,
    WebhookEventSyncType.PAYMENT_LIST_GATEWAYS: PaymentListGateways,
    WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED: (
        TransactionCancelationRequested
    ),
    WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED: TransactionChargeRequested,
    WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED: TransactionRefundRequested,
    WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS: OrderFilterShippingMethods,
    WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS: (
        CheckoutFilterShippingMethods
    ),
    WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT: (
        ShippingListMethodsForCheckout
    ),
    WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES: CalculateTaxes,
    WebhookEventSyncType.ORDER_CALCULATE_TAXES: CalculateTaxes,
    WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION: (
        PaymentGatewayInitializeSession
    ),
    WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION: TransactionInitializeSession,
    WebhookEventSyncType.TRANSACTION_PROCESS_SESSION: TransactionProcessSession,
    WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS: ListStoredPaymentMethods,
    WebhookEventSyncType.STORED_PAYMENT_METHOD_DELETE_REQUESTED: (
        StoredPaymentMethodDeleteRequested
    ),
    WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION: (
        PaymentGatewayInitializeTokenizationSession
    ),
    WebhookEventSyncType.PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION: (
        PaymentMethodInitializeTokenizationSession
    ),
    WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION: (
        PaymentMethodProcessTokenizationSession
    ),
}


ASYNC_WEBHOOK_TYPES_MAP = {
    WebhookEventAsyncType.ACCOUNT_CONFIRMATION_REQUESTED: AccountConfirmationRequested,
    WebhookEventAsyncType.ACCOUNT_CHANGE_EMAIL_REQUESTED: AccountChangeEmailRequested,
    WebhookEventAsyncType.ACCOUNT_EMAIL_CHANGED: AccountEmailChanged,
    WebhookEventAsyncType.ACCOUNT_SET_PASSWORD_REQUESTED: AccountSetPasswordRequested,
    WebhookEventAsyncType.ACCOUNT_CONFIRMED: AccountConfirmed,
    WebhookEventAsyncType.ACCOUNT_DELETE_REQUESTED: AccountDeleteRequested,
    WebhookEventAsyncType.ACCOUNT_DELETED: AccountDeleted,
    WebhookEventAsyncType.ADDRESS_CREATED: AddressCreated,
    WebhookEventAsyncType.ADDRESS_UPDATED: AddressUpdated,
    WebhookEventAsyncType.ADDRESS_DELETED: AddressDeleted,
    WebhookEventAsyncType.APP_INSTALLED: AppInstalled,
    WebhookEventAsyncType.APP_UPDATED: AppUpdated,
    WebhookEventAsyncType.APP_DELETED: AppDeleted,
    WebhookEventAsyncType.APP_STATUS_CHANGED: AppStatusChanged,
    WebhookEventAsyncType.ATTRIBUTE_CREATED: AttributeCreated,
    WebhookEventAsyncType.ATTRIBUTE_UPDATED: AttributeUpdated,
    WebhookEventAsyncType.ATTRIBUTE_DELETED: AttributeDeleted,
    WebhookEventAsyncType.ATTRIBUTE_VALUE_CREATED: AttributeValueCreated,
    WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED: AttributeValueUpdated,
    WebhookEventAsyncType.ATTRIBUTE_VALUE_DELETED: AttributeValueDeleted,
    WebhookEventAsyncType.CATEGORY_CREATED: CategoryCreated,
    WebhookEventAsyncType.CATEGORY_UPDATED: CategoryUpdated,
    WebhookEventAsyncType.CATEGORY_DELETED: CategoryDeleted,
    WebhookEventAsyncType.CHANNEL_CREATED: ChannelCreated,
    WebhookEventAsyncType.CHANNEL_UPDATED: ChannelUpdated,
    WebhookEventAsyncType.CHANNEL_DELETED: ChannelDeleted,
    WebhookEventAsyncType.CHANNEL_STATUS_CHANGED: ChannelStatusChanged,
    WebhookEventAsyncType.CHANNEL_METADATA_UPDATED: ChannelMetadataUpdated,
    WebhookEventAsyncType.GIFT_CARD_CREATED: GiftCardCreated,
    WebhookEventAsyncType.GIFT_CARD_UPDATED: GiftCardUpdated,
    WebhookEventAsyncType.GIFT_CARD_DELETED: GiftCardDeleted,
    WebhookEventAsyncType.GIFT_CARD_SENT: GiftCardSent,
    WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED: GiftCardStatusChanged,
    WebhookEventAsyncType.GIFT_CARD_METADATA_UPDATED: GiftCardMetadataUpdated,
    WebhookEventAsyncType.GIFT_CARD_EXPORT_COMPLETED: GiftCardExportCompleted,
    WebhookEventAsyncType.MENU_CREATED: MenuCreated,
    WebhookEventAsyncType.MENU_UPDATED: MenuUpdated,
    WebhookEventAsyncType.MENU_DELETED: MenuDeleted,
    WebhookEventAsyncType.MENU_ITEM_CREATED: MenuItemCreated,
    WebhookEventAsyncType.MENU_ITEM_UPDATED: MenuItemUpdated,
    WebhookEventAsyncType.MENU_ITEM_DELETED: MenuItemDeleted,
    WebhookEventAsyncType.ORDER_CREATED: OrderCreated,
    WebhookEventAsyncType.ORDER_UPDATED: OrderUpdated,
    WebhookEventAsyncType.ORDER_CONFIRMED: OrderConfirmed,
    WebhookEventAsyncType.ORDER_FULLY_PAID: OrderFullyPaid,
    WebhookEventAsyncType.ORDER_PAID: OrderPaid,
    WebhookEventAsyncType.ORDER_REFUNDED: OrderRefunded,
    WebhookEventAsyncType.ORDER_FULLY_REFUNDED: OrderFullyRefunded,
    WebhookEventAsyncType.ORDER_FULFILLED: OrderFulfilled,
    WebhookEventAsyncType.ORDER_CANCELLED: OrderCancelled,
    WebhookEventAsyncType.ORDER_EXPIRED: OrderExpired,
    WebhookEventAsyncType.ORDER_METADATA_UPDATED: OrderMetadataUpdated,
    WebhookEventAsyncType.ORDER_BULK_CREATED: OrderBulkCreated,
    WebhookEventAsyncType.DRAFT_ORDER_CREATED: DraftOrderCreated,
    WebhookEventAsyncType.DRAFT_ORDER_UPDATED: DraftOrderUpdated,
    WebhookEventAsyncType.DRAFT_ORDER_DELETED: DraftOrderDeleted,
    WebhookEventAsyncType.PRODUCT_CREATED: ProductCreated,
    WebhookEventAsyncType.PRODUCT_UPDATED: ProductUpdated,
    WebhookEventAsyncType.PRODUCT_DELETED: ProductDeleted,
    WebhookEventAsyncType.PRODUCT_METADATA_UPDATED: ProductMetadataUpdated,
    WebhookEventAsyncType.PRODUCT_EXPORT_COMPLETED: ProductExportCompleted,
    WebhookEventAsyncType.PRODUCT_MEDIA_CREATED: ProductMediaCreated,
    WebhookEventAsyncType.PRODUCT_MEDIA_UPDATED: ProductMediaUpdated,
    WebhookEventAsyncType.PRODUCT_MEDIA_DELETED: ProductMediaDeleted,
    WebhookEventAsyncType.PRODUCT_VARIANT_CREATED: ProductVariantCreated,
    WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED: ProductVariantUpdated,
    WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK: ProductVariantOutOfStock,
    WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK: ProductVariantBackInStock,
    WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED: ProductVariantStockUpdated,
    WebhookEventAsyncType.PRODUCT_VARIANT_DELETED: ProductVariantDeleted,
    WebhookEventAsyncType.PRODUCT_VARIANT_METADATA_UPDATED: (
        ProductVariantMetadataUpdated
    ),
    WebhookEventAsyncType.SALE_CREATED: SaleCreated,
    WebhookEventAsyncType.SALE_UPDATED: SaleUpdated,
    WebhookEventAsyncType.SALE_DELETED: SaleDeleted,
    WebhookEventAsyncType.SALE_TOGGLE: SaleToggle,
    WebhookEventAsyncType.PROMOTION_CREATED: PromotionCreated,
    WebhookEventAsyncType.PROMOTION_UPDATED: PromotionUpdated,
    WebhookEventAsyncType.PROMOTION_DELETED: PromotionDeleted,
    WebhookEventAsyncType.PROMOTION_STARTED: PromotionStarted,
    WebhookEventAsyncType.PROMOTION_ENDED: PromotionEnded,
    WebhookEventAsyncType.PROMOTION_RULE_CREATED: PromotionRuleCreated,
    WebhookEventAsyncType.PROMOTION_RULE_UPDATED: PromotionRuleUpdated,
    WebhookEventAsyncType.PROMOTION_RULE_DELETED: PromotionRuleDeleted,
    WebhookEventAsyncType.INVOICE_REQUESTED: InvoiceRequested,
    WebhookEventAsyncType.INVOICE_DELETED: InvoiceDeleted,
    WebhookEventAsyncType.INVOICE_SENT: InvoiceSent,
    WebhookEventAsyncType.FULFILLMENT_CREATED: FulfillmentCreated,
    WebhookEventAsyncType.FULFILLMENT_TRACKING_NUMBER_UPDATED: FulfillmentTrackingNumberUpdated,  # noqa: E501
    WebhookEventAsyncType.FULFILLMENT_CANCELED: FulfillmentCanceled,
    WebhookEventAsyncType.FULFILLMENT_APPROVED: FulfillmentApproved,
    WebhookEventAsyncType.FULFILLMENT_METADATA_UPDATED: FulfillmentMetadataUpdated,
    WebhookEventAsyncType.CUSTOMER_CREATED: CustomerCreated,
    WebhookEventAsyncType.CUSTOMER_UPDATED: CustomerUpdated,
    WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED: CustomerMetadataUpdated,
    WebhookEventAsyncType.COLLECTION_CREATED: CollectionCreated,
    WebhookEventAsyncType.COLLECTION_UPDATED: CollectionUpdated,
    WebhookEventAsyncType.COLLECTION_DELETED: CollectionDeleted,
    WebhookEventAsyncType.COLLECTION_METADATA_UPDATED: CollectionMetadataUpdated,
    WebhookEventAsyncType.CHECKOUT_CREATED: CheckoutCreated,
    WebhookEventAsyncType.CHECKOUT_UPDATED: CheckoutUpdated,
    WebhookEventAsyncType.CHECKOUT_FULLY_PAID: CheckoutFullyPaid,
    WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED: CheckoutMetadataUpdated,
    WebhookEventAsyncType.PAGE_CREATED: PageCreated,
    WebhookEventAsyncType.PAGE_UPDATED: PageUpdated,
    WebhookEventAsyncType.PAGE_DELETED: PageDeleted,
    WebhookEventAsyncType.PAGE_TYPE_CREATED: PageTypeCreated,
    WebhookEventAsyncType.PAGE_TYPE_UPDATED: PageTypeUpdated,
    WebhookEventAsyncType.PAGE_TYPE_DELETED: PageTypeDeleted,
    WebhookEventAsyncType.PERMISSION_GROUP_CREATED: PermissionGroupCreated,
    WebhookEventAsyncType.PERMISSION_GROUP_UPDATED: PermissionGroupUpdated,
    WebhookEventAsyncType.PERMISSION_GROUP_DELETED: PermissionGroupDeleted,
    WebhookEventAsyncType.SHIPPING_PRICE_CREATED: ShippingPriceCreated,
    WebhookEventAsyncType.SHIPPING_PRICE_UPDATED: ShippingPriceUpdated,
    WebhookEventAsyncType.SHIPPING_PRICE_DELETED: ShippingPriceDeleted,
    WebhookEventAsyncType.SHIPPING_ZONE_CREATED: ShippingZoneCreated,
    WebhookEventAsyncType.SHIPPING_ZONE_UPDATED: ShippingZoneUpdated,
    WebhookEventAsyncType.SHIPPING_ZONE_DELETED: ShippingZoneDeleted,
    WebhookEventAsyncType.SHIPPING_ZONE_METADATA_UPDATED: ShippingZoneMetadataUpdated,
    WebhookEventAsyncType.SHOP_METADATA_UPDATED: ShopMetadataUpdated,
    WebhookEventAsyncType.STAFF_CREATED: StaffCreated,
    WebhookEventAsyncType.STAFF_UPDATED: StaffUpdated,
    WebhookEventAsyncType.STAFF_DELETED: StaffDeleted,
    WebhookEventAsyncType.STAFF_SET_PASSWORD_REQUESTED: StaffSetPasswordRequested,
    WebhookEventAsyncType.TRANSACTION_ITEM_METADATA_UPDATED: (
        TransactionItemMetadataUpdated
    ),
    WebhookEventAsyncType.TRANSLATION_CREATED: TranslationCreated,
    WebhookEventAsyncType.TRANSLATION_UPDATED: TranslationUpdated,
    WebhookEventAsyncType.VOUCHER_CREATED: VoucherCreated,
    WebhookEventAsyncType.VOUCHER_UPDATED: VoucherUpdated,
    WebhookEventAsyncType.VOUCHER_DELETED: VoucherDeleted,
    WebhookEventAsyncType.VOUCHER_CODES_CREATED: VoucherCodesCreated,
    WebhookEventAsyncType.VOUCHER_CODES_DELETED: VoucherCodesDeleted,
    WebhookEventAsyncType.VOUCHER_METADATA_UPDATED: VoucherMetadataUpdated,
    WebhookEventAsyncType.VOUCHER_CODE_EXPORT_COMPLETED: VoucherCodeExportCompleted,
    WebhookEventAsyncType.WAREHOUSE_CREATED: WarehouseCreated,
    WebhookEventAsyncType.WAREHOUSE_UPDATED: WarehouseUpdated,
    WebhookEventAsyncType.WAREHOUSE_DELETED: WarehouseDeleted,
    WebhookEventAsyncType.WAREHOUSE_METADATA_UPDATED: WarehouseMetadataUpdated,
    WebhookEventAsyncType.THUMBNAIL_CREATED: ThumbnailCreated,
}

WEBHOOK_TYPES_MAP = ASYNC_WEBHOOK_TYPES_MAP | SYNC_WEBHOOK_TYPES_MAP
