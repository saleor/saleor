import graphene
from django.utils import timezone
from graphene import AbstractType, Union
from rx import Observable

from ... import __version__
from ...account.models import User
from ...attribute.models import AttributeTranslation, AttributeValueTranslation
from ...core.prices import quantize_price
from ...discount.models import SaleTranslation, VoucherTranslation
from ...menu.models import MenuItemTranslation
from ...order.utils import get_all_shipping_methods_for_order
from ...page.models import PageTranslation
from ...payment.interface import TransactionActionData
from ...product.models import (
    CategoryTranslation,
    CollectionTranslation,
    ProductTranslation,
    ProductVariantTranslation,
)
from ...shipping.models import ShippingMethodTranslation
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..account.types import User as UserType
from ..app.types import App as AppType
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByIdLoader
from ..core import ResolveInfo
from ..core.descriptions import (
    ADDED_IN_32,
    ADDED_IN_34,
    ADDED_IN_35,
    ADDED_IN_36,
    ADDED_IN_37,
    ADDED_IN_38,
    ADDED_IN_310,
    PREVIEW_FEATURE,
)
from ..core.scalars import PositiveDecimal
from ..core.types import EventObjectType, NonNullList
from ..order.dataloaders import OrderByIdLoader
from ..payment.enums import TransactionActionEnum
from ..payment.types import TransactionItem
from ..plugins.dataloaders import plugin_manager_promise_callback
from ..shipping.dataloaders import ShippingMethodChannelListingByChannelSlugLoader
from ..shipping.types import ShippingMethod
from ..translations import types as translation_types
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
    SaleTranslation: translation_types.SaleTranslation,
    VoucherTranslation: translation_types.VoucherTranslation,
    MenuItemTranslation: translation_types.MenuItemTranslation,
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
    issued_at = graphene.DateTime(description="Time of the event.")
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
    def resolve_issued_at(_root, _info: ResolveInfo):
        return timezone.now()

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


class AddressBase(AbstractType):
    address = graphene.Field(
        "saleor.graphql.account.types.Address",
        description="The address the event relates to.",
    )

    @staticmethod
    def resolve_address(root, _info: ResolveInfo):
        _, address = root
        return address


class AddressCreated(EventObjectType, AddressBase):
    class Meta:
        dry_run_model_name = "Address"
        interfaces = (Event,)
        description = (
            "Event sent when new address is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AddressUpdated(EventObjectType, AddressBase):
    class Meta:
        dry_run_model_name = "Address"
        interfaces = (Event,)
        description = (
            "Event sent when address is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AddressDeleted(EventObjectType, AddressBase):
    class Meta:
        dry_run_model_name = "Address"
        interfaces = (Event,)
        description = (
            "Event sent when address is deleted." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AppBase(AbstractType):
    app = graphene.Field(
        "saleor.graphql.app.types.App",
        description="The application the event relates to.",
    )

    @staticmethod
    def resolve_app(root, _info: ResolveInfo):
        _, app = root
        return app


class AppInstalled(EventObjectType, AppBase):
    class Meta:
        dry_run_model_name = "App"
        interfaces = (Event,)
        description = (
            "Event sent when new app is installed." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class AppUpdated(EventObjectType, AppBase):
    class Meta:
        dry_run_model_name = "App"
        interfaces = (Event,)
        description = "Event sent when app is updated." + ADDED_IN_34 + PREVIEW_FEATURE


class AppDeleted(EventObjectType, AppBase):
    class Meta:
        dry_run_model_name = "App"
        interfaces = (Event,)
        description = "Event sent when app is deleted." + ADDED_IN_34 + PREVIEW_FEATURE


class AppStatusChanged(EventObjectType, AppBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when app status has changed." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class AttributeBase(AbstractType):
    attribute = graphene.Field(
        "saleor.graphql.attribute.types.Attribute",
        description="The attribute the event relates to.",
    )

    @staticmethod
    def resolve_attribute(root, _info: ResolveInfo):
        _, attribute = root
        return attribute


class AttributeCreated(EventObjectType, AttributeBase):
    class Meta:
        dry_run_model_name = "Attribute"
        interfaces = (Event,)
        description = (
            "Event sent when new attribute is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AttributeUpdated(EventObjectType, AttributeBase):
    class Meta:
        dry_run_model_name = "Attribute"
        interfaces = (Event,)
        description = (
            "Event sent when attribute is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AttributeDeleted(EventObjectType, AttributeBase):
    class Meta:
        dry_run_model_name = "Attribute"
        interfaces = (Event,)
        description = (
            "Event sent when attribute is deleted." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AttributeValueBase(AbstractType):
    attribute_value = graphene.Field(
        "saleor.graphql.attribute.types.AttributeValue",
        description="The attribute value the event relates to.",
    )

    @staticmethod
    def resolve_attribute_value(root, _info: ResolveInfo):
        _, attribute = root
        return attribute


class AttributeValueCreated(EventObjectType, AttributeValueBase):
    class Meta:
        dry_run_model_name = "Attribute"
        interfaces = (Event,)
        description = (
            "Event sent when new attribute value is created."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )


class AttributeValueUpdated(EventObjectType, AttributeValueBase):
    class Meta:
        dry_run_model_name = "Attribute"
        interfaces = (Event,)
        description = (
            "Event sent when attribute value is updated."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )


class AttributeValueDeleted(EventObjectType, AttributeValueBase):
    class Meta:
        dry_run_model_name = "Attribute"
        interfaces = (Event,)
        description = (
            "Event sent when attribute value is deleted."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )


class CategoryBase(AbstractType):
    category = graphene.Field(
        "saleor.graphql.product.types.Category",
        description="The category the event relates to.",
    )

    @staticmethod
    def resolve_category(root, info: ResolveInfo):
        _, category = root
        return category


class CategoryCreated(EventObjectType, CategoryBase):
    class Meta:
        dry_run_model_name = "Category"
        interfaces = (Event,)
        description = (
            "Event sent when new category is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CategoryUpdated(EventObjectType, CategoryBase):
    class Meta:
        dry_run_model_name = "Category"
        interfaces = (Event,)
        description = (
            "Event sent when category is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CategoryDeleted(EventObjectType, CategoryBase):
    class Meta:
        dry_run_model_name = "Category"
        interfaces = (Event,)
        description = (
            "Event sent when category is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelBase(AbstractType):
    channel = graphene.Field(
        "saleor.graphql.channel.types.Channel",
        description="The channel the event relates to.",
    )

    @staticmethod
    def resolve_channel(root, info: ResolveInfo):
        _, channel = root
        return channel


class ChannelCreated(EventObjectType, ChannelBase):
    class Meta:
        dry_run_model_name = "Channel"
        interfaces = (Event,)
        description = (
            "Event sent when new channel is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelUpdated(EventObjectType, ChannelBase):
    class Meta:
        dry_run_model_name = "Channel"
        interfaces = (Event,)
        description = (
            "Event sent when channel is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelDeleted(EventObjectType, ChannelBase):
    class Meta:
        dry_run_model_name = "Channel"
        interfaces = (Event,)
        description = (
            "Event sent when channel is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelStatusChanged(EventObjectType, ChannelBase):
    class Meta:
        dry_run_model_name = "Channel"
        interfaces = (Event,)
        description = (
            "Event sent when channel status has changed."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class OrderBase(AbstractType):
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="The order the event relates to.",
    )

    @staticmethod
    def resolve_order(root, info: ResolveInfo):
        _, order = root
        return order


class OrderCreated(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when new order is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderUpdated(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when order is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderConfirmed(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when order is confirmed." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderFullyPaid(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when order is fully paid." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderFulfilled(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when order is fulfilled." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderCancelled(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when order is canceled." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderMetadataUpdated(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when order metadata is updated." + ADDED_IN_38 + PREVIEW_FEATURE
        )


class DraftOrderCreated(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when new draft order is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class DraftOrderUpdated(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when draft order is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class DraftOrderDeleted(EventObjectType, OrderBase):
    class Meta:
        dry_run_model_name = "Order"
        interfaces = (Event,)
        description = (
            "Event sent when draft order is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardBase(AbstractType):
    gift_card = graphene.Field(
        "saleor.graphql.giftcard.types.GiftCard",
        description="The gift card the event relates to.",
    )

    @staticmethod
    def resolve_gift_card(root, info: ResolveInfo):
        _, gift_card = root
        return gift_card


class GiftCardCreated(EventObjectType, GiftCardBase):
    class Meta:
        dry_run_model_name = "GiftCard"
        interfaces = (Event,)
        description = (
            "Event sent when new gift card is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardUpdated(EventObjectType, GiftCardBase):
    class Meta:
        dry_run_model_name = "GiftCard"
        interfaces = (Event,)
        description = (
            "Event sent when gift card is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardDeleted(EventObjectType, GiftCardBase):
    class Meta:
        dry_run_model_name = "GiftCard"
        interfaces = (Event,)
        description = (
            "Event sent when gift card is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardStatusChanged(EventObjectType, GiftCardBase):
    class Meta:
        dry_run_model_name = "GiftCard"
        interfaces = (Event,)
        description = (
            "Event sent when gift card status has changed."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class GiftCardMetadataUpdated(EventObjectType, GiftCardBase):
    class Meta:
        dry_run_model_name = "GiftCard"
        interfaces = (Event,)
        description = (
            "Event sent when gift card metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


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


class MenuCreated(EventObjectType, MenuBase):
    class Meta:
        dry_run_model_name = "Menu"
        interfaces = (Event,)
        description = (
            "Event sent when new menu is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuUpdated(EventObjectType, MenuBase):
    class Meta:
        dry_run_model_name = "Menu"
        interfaces = (Event,)
        description = "Event sent when menu is updated." + ADDED_IN_34 + PREVIEW_FEATURE


class MenuDeleted(EventObjectType, MenuBase):
    class Meta:
        dry_run_model_name = "Menu"
        interfaces = (Event,)
        description = "Event sent when menu is deleted." + ADDED_IN_34 + PREVIEW_FEATURE


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


class MenuItemCreated(EventObjectType, MenuItemBase):
    class Meta:
        dry_run_model_name = "MenuItem"
        interfaces = (Event,)
        description = (
            "Event sent when new menu item is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuItemUpdated(EventObjectType, MenuItemBase):
    class Meta:
        dry_run_model_name = "MenuItem"
        interfaces = (Event,)
        description = (
            "Event sent when menu item is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuItemDeleted(EventObjectType, MenuItemBase):
    class Meta:
        dry_run_model_name = "MenuItem"
        interfaces = (Event,)
        description = (
            "Event sent when menu item is deleted." + ADDED_IN_34 + PREVIEW_FEATURE
        )


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


class ProductCreated(EventObjectType, ProductBase):
    class Meta:
        dry_run_model_name = "Product"
        interfaces = (Event,)
        description = (
            "Event sent when new product is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ProductUpdated(EventObjectType, ProductBase):
    class Meta:
        dry_run_model_name = "Product"
        interfaces = (Event,)
        description = (
            "Event sent when product is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ProductDeleted(EventObjectType, ProductBase):
    class Meta:
        dry_run_model_name = "Product"
        interfaces = (Event,)
        description = (
            "Event sent when product is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ProductMetadataUpdated(EventObjectType, ProductBase):
    class Meta:
        dry_run_model_name = "Product"
        interfaces = (Event,)
        description = (
            "Event sent when product metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


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


class ProductVariantCreated(EventObjectType, ProductVariantBase):
    class Meta:
        dry_run_model_name = "Product"
        interfaces = (Event,)
        description = (
            "Event sent when new product variant is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantUpdated(EventObjectType, ProductVariantBase):
    class Meta:
        dry_run_model_name = "Product"
        interfaces = (Event,)
        description = (
            "Event sent when product variant is updated."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantDeleted(EventObjectType, ProductVariantBase):
    class Meta:
        dry_run_model_name = "Product"
        interfaces = (Event,)
        description = (
            "Event sent when product variant is deleted."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantMetadataUpdated(EventObjectType, ProductVariantBase):
    class Meta:
        dry_run_model_name = "Product"
        interfaces = (Event,)
        description = (
            "Event sent when product variant metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class ProductVariantOutOfStock(EventObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        dry_run_model_name = "Stock"
        interfaces = (Event,)
        description = (
            "Event sent when product variant is out of stock."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )

    @staticmethod
    def resolve_product_variant(root, info: ResolveInfo, channel=None):
        _, stock = root
        variant = stock.product_variant
        return ChannelContext(node=variant, channel_slug=channel)

    @staticmethod
    def resolve_warehouse(root, _info: ResolveInfo):
        _, stock = root
        return stock.warehouse


class ProductVariantBackInStock(EventObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        dry_run_model_name = "Stock"
        interfaces = (Event,)
        description = (
            "Event sent when product variant is back in stock."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )

    @staticmethod
    def resolve_product_variant(root, _info: ResolveInfo, channel=None):
        _, stock = root
        variant = stock.product_variant
        return ChannelContext(node=variant, channel_slug=channel)

    @staticmethod
    def resolve_warehouse(root, _info):
        _, stock = root
        return stock.warehouse


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


class SaleCreated(EventObjectType, SaleBase):
    class Meta:
        dry_run_model_name = "Sale"
        interfaces = (Event,)
        description = (
            "Event sent when new sale is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class SaleUpdated(EventObjectType, SaleBase):
    class Meta:
        dry_run_model_name = "Sale"
        interfaces = (Event,)
        description = "Event sent when sale is updated." + ADDED_IN_32 + PREVIEW_FEATURE


class SaleDeleted(EventObjectType, SaleBase):
    class Meta:
        dry_run_model_name = "Sale"
        interfaces = (Event,)
        description = "Event sent when sale is deleted." + ADDED_IN_32 + PREVIEW_FEATURE


class SaleToggle(EventObjectType, SaleBase):
    sale = graphene.Field(
        "saleor.graphql.discount.types.Sale",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The sale the event relates to." + ADDED_IN_35 + PREVIEW_FEATURE,
    )

    class Meta:
        dry_run_model_name = "Sale"
        description = (
            "The event informs about the start or end of the sale."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )
        interfaces = (Event,)


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


class InvoiceRequested(EventObjectType, InvoiceBase):
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        required=True,
        description="Order related to the invoice." + ADDED_IN_310,
    )

    class Meta:
        dry_run_model_name = "Invoice"
        interfaces = (Event,)
        description = (
            "Event sent when invoice is requested." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class InvoiceDeleted(EventObjectType, InvoiceBase):
    class Meta:
        dry_run_model_name = "Invoice"
        interfaces = (Event,)
        description = (
            "Event sent when invoice is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class InvoiceSent(EventObjectType, InvoiceBase):
    class Meta:
        dry_run_model_name = "Invoice"
        interfaces = (Event,)
        description = "Event sent when invoice is sent." + ADDED_IN_32 + PREVIEW_FEATURE


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


class FulfillmentCreated(EventObjectType, FulfillmentBase):
    class Meta:
        dry_run_model_name = "Fulfillment"
        interfaces = (Event,)
        description = (
            "Event sent when new fulfillment is created."
            + ADDED_IN_34
            + PREVIEW_FEATURE
        )


class FulfillmentCanceled(EventObjectType, FulfillmentBase):
    class Meta:
        dry_run_model_name = "Fulfillment"
        interfaces = (Event,)
        description = (
            "Event sent when fulfillment is canceled." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class FulfillmentApproved(EventObjectType, FulfillmentBase):
    class Meta:
        dry_run_model_name = "Fulfillment"
        interfaces = (Event,)
        description = (
            "Event sent when fulfillment is approved." + ADDED_IN_37 + PREVIEW_FEATURE
        )


class FulfillmentMetadataUpdated(EventObjectType, FulfillmentBase):
    class Meta:
        dry_run_model_name = "Fulfillment"
        interfaces = (Event,)
        description = (
            "Event sent when fulfillment metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class UserBase(AbstractType):
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The user the event relates to.",
    )

    @staticmethod
    def resolve_user(root, _info: ResolveInfo):
        _, user = root
        return user


class CustomerCreated(EventObjectType, UserBase):
    class Meta:
        dry_run_model_name = "User"
        interfaces = (Event,)
        description = (
            "Event sent when new customer user is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class CustomerUpdated(EventObjectType, UserBase):
    class Meta:
        dry_run_model_name = "User"
        interfaces = (Event,)
        description = (
            "Event sent when customer user is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CustomerMetadataUpdated(EventObjectType, UserBase):
    class Meta:
        dry_run_model_name = "User"
        interfaces = (Event,)
        description = (
            "Event sent when customer user metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


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


class CollectionCreated(EventObjectType, CollectionBase):
    class Meta:
        dry_run_model_name = "Collection"
        interfaces = (Event,)
        description = (
            "Event sent when new collection is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionUpdated(EventObjectType, CollectionBase):
    class Meta:
        dry_run_model_name = "Collection"
        interfaces = (Event,)
        description = (
            "Event sent when collection is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionDeleted(EventObjectType, CollectionBase):
    class Meta:
        dry_run_model_name = "Collection"
        interfaces = (Event,)
        description = (
            "Event sent when collection is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionMetadataUpdated(EventObjectType, CollectionBase):
    class Meta:
        dry_run_model_name = "Collection"
        interfaces = (Event,)
        description = (
            "Event sent when collection metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class CheckoutBase(AbstractType):
    checkout = graphene.Field(
        "saleor.graphql.checkout.types.Checkout",
        description="The checkout the event relates to.",
    )

    @staticmethod
    def resolve_checkout(root, _info: ResolveInfo):
        _, checkout = root
        return checkout


class CheckoutCreated(EventObjectType, CheckoutBase):
    class Meta:
        dry_run_model_name = "Checkout"
        interfaces = (Event,)
        description = (
            "Event sent when new checkout is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CheckoutUpdated(EventObjectType, CheckoutBase):
    class Meta:
        dry_run_model_name = "Checkout"
        interfaces = (Event,)
        description = (
            "Event sent when checkout is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CheckoutMetadataUpdated(EventObjectType, CheckoutBase):
    class Meta:
        dry_run_model_name = "Checkout"
        interfaces = (Event,)
        description = (
            "Event sent when checkout metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class PageBase(AbstractType):
    page = graphene.Field(
        "saleor.graphql.page.types.Page", description="The page the event relates to."
    )

    @staticmethod
    def resolve_page(root, _info: ResolveInfo):
        _, page = root
        return page


class PageCreated(EventObjectType, PageBase):
    class Meta:
        dry_run_model_name = "Page"
        interfaces = (Event,)
        description = (
            "Event sent when new page is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class PageUpdated(EventObjectType, PageBase):
    class Meta:
        dry_run_model_name = "Page"
        interfaces = (Event,)
        description = "Event sent when page is updated." + ADDED_IN_32 + PREVIEW_FEATURE


class PageDeleted(EventObjectType, PageBase):
    class Meta:
        dry_run_model_name = "Page"
        interfaces = (Event,)
        description = "Event sent when page is deleted." + ADDED_IN_32 + PREVIEW_FEATURE


class PageTypeBase(AbstractType):
    page_type = graphene.Field(
        "saleor.graphql.page.types.PageType",
        description="The page type the event relates to.",
    )

    @staticmethod
    def resolve_page_type(root, _info: ResolveInfo):
        _, page_type = root
        return page_type


class PageTypeCreated(EventObjectType, PageTypeBase):
    class Meta:
        dry_run_model_name = "PageType"
        interfaces = (Event,)
        description = (
            "Event sent when new page type is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class PageTypeUpdated(EventObjectType, PageTypeBase):
    class Meta:
        dry_run_model_name = "PageType"
        interfaces = (Event,)
        description = (
            "Event sent when page type is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class PageTypeDeleted(EventObjectType, PageTypeBase):
    class Meta:
        dry_run_model_name = "PageType"
        interfaces = (Event,)
        description = (
            "Event sent when page type is deleted." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class PermissionGroupBase(AbstractType):
    permission_group = graphene.Field(
        "saleor.graphql.account.types.Group",
        description="The permission group the event relates to.",
    )

    @staticmethod
    def resolve_permission_group(root, _info: ResolveInfo):
        _, permission_group = root
        return permission_group


class PermissionGroupCreated(EventObjectType, PermissionGroupBase):
    class Meta:
        dry_run_model_name = "PermissionGroup"
        interfaces = (Event,)
        description = (
            "Event sent when new permission group is created."
            + ADDED_IN_36
            + PREVIEW_FEATURE
        )


class PermissionGroupUpdated(EventObjectType, PermissionGroupBase):
    class Meta:
        dry_run_model_name = "PermissionGroup"
        interfaces = (Event,)
        description = (
            "Event sent when permission group is updated."
            + ADDED_IN_36
            + PREVIEW_FEATURE
        )


class PermissionGroupDeleted(EventObjectType, PermissionGroupBase):
    class Meta:
        dry_run_model_name = "PermissionGroup"
        interfaces = (Event,)
        description = (
            "Event sent when permission group is deleted."
            + ADDED_IN_36
            + PREVIEW_FEATURE
        )


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


class ShippingPriceCreated(EventObjectType, ShippingPriceBase):
    class Meta:
        dry_run_model_name = "ShippingMethod"
        interfaces = (Event,)
        description = (
            "Event sent when new shipping price is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ShippingPriceUpdated(EventObjectType, ShippingPriceBase):
    class Meta:
        dry_run_model_name = "ShippingMethod"
        interfaces = (Event,)
        description = (
            "Event sent when shipping price is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ShippingPriceDeleted(EventObjectType, ShippingPriceBase):
    class Meta:
        dry_run_model_name = "ShippingMethod"
        interfaces = (Event,)
        description = (
            "Event sent when shipping price is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


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


class ShippingZoneCreated(EventObjectType, ShippingZoneBase):
    class Meta:
        dry_run_model_name = "ShippingZone"
        interfaces = (Event,)
        description = (
            "Event sent when new shipping zone is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ShippingZoneUpdated(EventObjectType, ShippingZoneBase):
    class Meta:
        dry_run_model_name = "ShippingZone"
        interfaces = (Event,)
        description = (
            "Event sent when shipping zone is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ShippingZoneDeleted(EventObjectType, ShippingZoneBase):
    class Meta:
        dry_run_model_name = "ShippingZone"
        interfaces = (Event,)
        description = (
            "Event sent when shipping zone is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ShippingZoneMetadataUpdated(EventObjectType, ShippingZoneBase):
    class Meta:
        dry_run_model_name = "ShippingZone"
        interfaces = (Event,)
        description = (
            "Event sent when shipping zone metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class StaffCreated(EventObjectType, UserBase):
    class Meta:
        dry_run_model_name = "User"
        interfaces = (Event,)
        description = (
            "Event sent when new staff user is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class StaffUpdated(EventObjectType, UserBase):
    class Meta:
        dry_run_model_name = "User"
        interfaces = (Event,)
        description = (
            "Event sent when staff user is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class StaffDeleted(EventObjectType, UserBase):
    class Meta:
        dry_run_model_name = "User"
        interfaces = (Event,)
        description = (
            "Event sent when staff user is deleted." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class TransactionAction(EventObjectType, AbstractType):
    action_type = graphene.Field(
        TransactionActionEnum,
        required=True,
        description="Determines the action type.",
    )
    amount = PositiveDecimal(
        description="Transaction request amount. Null when action type is VOID.",
    )

    @staticmethod
    def resolve_amount(root: TransactionActionData, _info: ResolveInfo):
        if root.action_value:
            return quantize_price(root.action_value, root.transaction.currency)
        return None


class TransactionActionRequest(EventObjectType):
    transaction = graphene.Field(
        TransactionItem,
        description="Look up a transaction." + ADDED_IN_34 + PREVIEW_FEATURE,
    )
    action = graphene.Field(
        TransactionAction,
        required=True,
        description="Requested action data." + ADDED_IN_34 + PREVIEW_FEATURE,
    )

    class Meta:
        dry_run_model_name = "TransactionActionData"
        interfaces = (Event,)
        description = (
            "Event sent when transaction action is requested."
            + ADDED_IN_34
            + PREVIEW_FEATURE
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


class TransactionItemMetadataUpdated(EventObjectType):
    transaction = graphene.Field(
        TransactionItem,
        description="Look up a transaction." + PREVIEW_FEATURE,
    )

    class Meta:
        dry_run_model_name = "TransactionItem"
        interfaces = (Event,)
        description = (
            "Event sent when transaction item metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )

    @staticmethod
    def resolve_transaction(root, _info: ResolveInfo):
        _, transaction_item = root
        return transaction_item


class TranslationTypes(Union):
    class Meta:
        types = tuple(TRANSLATIONS_TYPES_MAP.values())

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        instance_type = type(instance)
        if instance_type in TRANSLATIONS_TYPES_MAP:
            return TRANSLATIONS_TYPES_MAP[instance_type]

        return super(TranslationTypes, cls).resolve_type(instance, info)


class TranslationBase(AbstractType):
    translation = graphene.Field(
        TranslationTypes, description="The translation the event relates to."
    )

    @staticmethod
    def resolve_translation(root, _info: ResolveInfo):
        _, translation = root
        return translation


class TranslationCreated(EventObjectType, TranslationBase):
    class Meta:
        dry_run_model_name = "Translation"
        interfaces = (Event,)
        description = (
            "Event sent when new translation is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class TranslationUpdated(EventObjectType, TranslationBase):
    class Meta:
        dry_run_model_name = "Translation"
        interfaces = (Event,)
        description = (
            "Event sent when translation is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


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


class VoucherCreated(EventObjectType, VoucherBase):
    class Meta:
        dry_run_model_name = "Voucher"
        interfaces = (Event,)
        description = (
            "Event sent when new voucher is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class VoucherUpdated(EventObjectType, VoucherBase):
    class Meta:
        dry_run_model_name = "Voucher"
        interfaces = (Event,)
        description = (
            "Event sent when voucher is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class VoucherDeleted(EventObjectType, VoucherBase):
    class Meta:
        dry_run_model_name = "Voucher"
        interfaces = (Event,)
        description = (
            "Event sent when voucher is deleted." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class VoucherMetadataUpdated(EventObjectType, VoucherBase):
    class Meta:
        dry_run_model_name = "Voucher"
        interfaces = (Event,)
        description = (
            "Event sent when voucher metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class PaymentBase(AbstractType):
    payment = graphene.Field(
        "saleor.graphql.payment.types.Payment",
        description="Look up a payment.",
    )

    @staticmethod
    def resolve_payment(root, _info: ResolveInfo):
        _, payment = root
        return payment


class PaymentAuthorize(EventObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Authorize payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentCaptureEvent(EventObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Capture payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentRefundEvent(EventObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Refund payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentVoidEvent(EventObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Void payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentConfirmEvent(EventObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Confirm payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentProcessEvent(EventObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Process payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentListGateways(EventObjectType, CheckoutBase):
    class Meta:
        interfaces = (Event,)
        description = "List payment gateways." + ADDED_IN_36 + PREVIEW_FEATURE


class ShippingListMethodsForCheckout(EventObjectType, CheckoutBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36
        + PREVIEW_FEATURE,
    )

    @staticmethod
    @plugin_manager_promise_callback
    def resolve_shipping_methods(root, info: ResolveInfo, manager):
        _, checkout = root
        return resolve_shipping_methods_for_checkout(info, checkout, manager)

    class Meta:
        interfaces = (Event,)
        description = (
            "List shipping methods for checkout." + ADDED_IN_36 + PREVIEW_FEATURE
        )


class CalculateTaxes(EventObjectType):
    tax_base = graphene.Field(
        "saleor.graphql.core.types.taxes.TaxableObject", required=True
    )

    class Meta:
        interfaces = (Event,)
        description = (
            "Synchronous webhook for calculating checkout/order taxes."
            + ADDED_IN_37
            + PREVIEW_FEATURE
        )

    def resolve_tax_base(root, _info: ResolveInfo):
        _, tax_base = root
        return tax_base


class CheckoutFilterShippingMethods(EventObjectType, CheckoutBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36
        + PREVIEW_FEATURE,
    )

    @staticmethod
    @plugin_manager_promise_callback
    def resolve_shipping_methods(root, info: ResolveInfo, manager):
        _, checkout = root
        return resolve_shipping_methods_for_checkout(info, checkout, manager)

    class Meta:
        interfaces = (Event,)
        description = (
            "Filter shipping methods for checkout." + ADDED_IN_36 + PREVIEW_FEATURE
        )


class OrderFilterShippingMethods(EventObjectType, OrderBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36
        + PREVIEW_FEATURE,
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
        interfaces = (Event,)
        description = (
            "Filter shipping methods for order." + ADDED_IN_36 + PREVIEW_FEATURE
        )


class WarehouseBase(AbstractType):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse",
        description="The warehouse the event relates to.",
    )

    @staticmethod
    def resolve_warehouse(root, _info: ResolveInfo):
        _, warehouse = root
        return warehouse


class WarehouseCreated(EventObjectType, WarehouseBase):
    class Meta:
        dry_run_model_name = "Warehouse"
        interfaces = (Event,)
        description = (
            "Event sent when new warehouse is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseUpdated(EventObjectType, WarehouseBase):
    class Meta:
        dry_run_model_name = "Warehouse"
        interfaces = (Event,)
        description = (
            "Event sent when warehouse is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseDeleted(EventObjectType, WarehouseBase):
    class Meta:
        dry_run_model_name = "Warehouse"
        interfaces = (Event,)
        description = (
            "Event sent when warehouse is deleted." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseMetadataUpdated(EventObjectType, WarehouseBase):
    class Meta:
        dry_run_model_name = "Warehouse"
        interfaces = (Event,)
        description = (
            "Event sent when warehouse metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class Subscription(EventObjectType):
    event = graphene.Field(
        Event,
        description="Look up subscription event." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_event(root, info: ResolveInfo):
        return Observable.from_([root])


WEBHOOK_TYPES_MAP = {
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
    WebhookEventAsyncType.GIFT_CARD_CREATED: GiftCardCreated,
    WebhookEventAsyncType.GIFT_CARD_UPDATED: GiftCardUpdated,
    WebhookEventAsyncType.GIFT_CARD_DELETED: GiftCardDeleted,
    WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED: GiftCardStatusChanged,
    WebhookEventAsyncType.GIFT_CARD_METADATA_UPDATED: GiftCardMetadataUpdated,
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
    WebhookEventAsyncType.ORDER_FULFILLED: OrderFulfilled,
    WebhookEventAsyncType.ORDER_CANCELLED: OrderCancelled,
    WebhookEventAsyncType.ORDER_METADATA_UPDATED: OrderMetadataUpdated,
    WebhookEventAsyncType.DRAFT_ORDER_CREATED: DraftOrderCreated,
    WebhookEventAsyncType.DRAFT_ORDER_UPDATED: DraftOrderUpdated,
    WebhookEventAsyncType.DRAFT_ORDER_DELETED: DraftOrderDeleted,
    WebhookEventAsyncType.PRODUCT_CREATED: ProductCreated,
    WebhookEventAsyncType.PRODUCT_UPDATED: ProductUpdated,
    WebhookEventAsyncType.PRODUCT_DELETED: ProductDeleted,
    WebhookEventAsyncType.PRODUCT_METADATA_UPDATED: ProductMetadataUpdated,
    WebhookEventAsyncType.PRODUCT_VARIANT_CREATED: ProductVariantCreated,
    WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED: ProductVariantUpdated,
    WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK: ProductVariantOutOfStock,
    WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK: ProductVariantBackInStock,
    WebhookEventAsyncType.PRODUCT_VARIANT_DELETED: ProductVariantDeleted,
    WebhookEventAsyncType.PRODUCT_VARIANT_METADATA_UPDATED: (
        ProductVariantMetadataUpdated
    ),
    WebhookEventAsyncType.SALE_CREATED: SaleCreated,
    WebhookEventAsyncType.SALE_UPDATED: SaleUpdated,
    WebhookEventAsyncType.SALE_DELETED: SaleDeleted,
    WebhookEventAsyncType.SALE_TOGGLE: SaleToggle,
    WebhookEventAsyncType.INVOICE_REQUESTED: InvoiceRequested,
    WebhookEventAsyncType.INVOICE_DELETED: InvoiceDeleted,
    WebhookEventAsyncType.INVOICE_SENT: InvoiceSent,
    WebhookEventAsyncType.FULFILLMENT_CREATED: FulfillmentCreated,
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
    WebhookEventAsyncType.STAFF_CREATED: StaffCreated,
    WebhookEventAsyncType.STAFF_UPDATED: StaffUpdated,
    WebhookEventAsyncType.STAFF_DELETED: StaffDeleted,
    WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST: TransactionActionRequest,
    WebhookEventAsyncType.TRANSACTION_ITEM_METADATA_UPDATED: (
        TransactionItemMetadataUpdated
    ),
    WebhookEventAsyncType.TRANSLATION_CREATED: TranslationCreated,
    WebhookEventAsyncType.TRANSLATION_UPDATED: TranslationUpdated,
    WebhookEventAsyncType.VOUCHER_CREATED: VoucherCreated,
    WebhookEventAsyncType.VOUCHER_UPDATED: VoucherUpdated,
    WebhookEventAsyncType.VOUCHER_DELETED: VoucherDeleted,
    WebhookEventAsyncType.VOUCHER_METADATA_UPDATED: VoucherMetadataUpdated,
    WebhookEventAsyncType.WAREHOUSE_CREATED: WarehouseCreated,
    WebhookEventAsyncType.WAREHOUSE_UPDATED: WarehouseUpdated,
    WebhookEventAsyncType.WAREHOUSE_DELETED: WarehouseDeleted,
    WebhookEventAsyncType.WAREHOUSE_METADATA_UPDATED: WarehouseMetadataUpdated,
    WebhookEventSyncType.PAYMENT_AUTHORIZE: PaymentAuthorize,
    WebhookEventSyncType.PAYMENT_CAPTURE: PaymentCaptureEvent,
    WebhookEventSyncType.PAYMENT_REFUND: PaymentRefundEvent,
    WebhookEventSyncType.PAYMENT_VOID: PaymentVoidEvent,
    WebhookEventSyncType.PAYMENT_CONFIRM: PaymentConfirmEvent,
    WebhookEventSyncType.PAYMENT_PROCESS: PaymentProcessEvent,
    WebhookEventSyncType.PAYMENT_LIST_GATEWAYS: PaymentListGateways,
    WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS: (OrderFilterShippingMethods),
    WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS: (
        CheckoutFilterShippingMethods
    ),
    WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT: (
        ShippingListMethodsForCheckout
    ),
    WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES: CalculateTaxes,
    WebhookEventSyncType.ORDER_CALCULATE_TAXES: CalculateTaxes,
}
