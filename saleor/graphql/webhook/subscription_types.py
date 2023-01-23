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
    ADDED_IN_311,
    PREVIEW_FEATURE,
)
from ..core.scalars import PositiveDecimal
from ..core.types import NonNullList, SubscriptionObjectType
from ..order.dataloaders import OrderByIdLoader
from ..payment.enums import TransactionActionEnum
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


class AddressCreated(SubscriptionObjectType, AddressBase):
    class Meta:
        root_type = "Address"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new address is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AddressUpdated(SubscriptionObjectType, AddressBase):
    class Meta:
        root_type = "Address"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when address is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AddressDeleted(SubscriptionObjectType, AddressBase):
    class Meta:
        root_type = "Address"
        enable_dry_run = True
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


class AppInstalled(SubscriptionObjectType, AppBase):
    class Meta:
        root_type = "App"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new app is installed." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class AppUpdated(SubscriptionObjectType, AppBase):
    class Meta:
        root_type = "App"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when app is updated." + ADDED_IN_34 + PREVIEW_FEATURE


class AppDeleted(SubscriptionObjectType, AppBase):
    class Meta:
        root_type = "App"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when app is deleted." + ADDED_IN_34 + PREVIEW_FEATURE


class AppStatusChanged(SubscriptionObjectType, AppBase):
    class Meta:
        root_type = "App"
        enable_dry_run = True
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


class AttributeCreated(SubscriptionObjectType, AttributeBase):
    class Meta:
        root_type = "Attribute"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new attribute is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AttributeUpdated(SubscriptionObjectType, AttributeBase):
    class Meta:
        root_type = "Attribute"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when attribute is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AttributeDeleted(SubscriptionObjectType, AttributeBase):
    class Meta:
        root_type = "Attribute"
        enable_dry_run = True
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


class AttributeValueCreated(SubscriptionObjectType, AttributeValueBase):
    class Meta:
        root_type = "AttributeValue"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new attribute value is created."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )


class AttributeValueUpdated(SubscriptionObjectType, AttributeValueBase):
    class Meta:
        root_type = "AttributeValue"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when attribute value is updated."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )


class AttributeValueDeleted(SubscriptionObjectType, AttributeValueBase):
    class Meta:
        root_type = "AttributeValue"
        enable_dry_run = True
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


class CategoryCreated(SubscriptionObjectType, CategoryBase):
    class Meta:
        root_type = "Category"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new category is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CategoryUpdated(SubscriptionObjectType, CategoryBase):
    class Meta:
        root_type = "Category"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when category is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CategoryDeleted(SubscriptionObjectType, CategoryBase):
    class Meta:
        root_type = "Category"
        enable_dry_run = True
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


class ChannelCreated(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new channel is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelUpdated(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when channel is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelDeleted(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when channel is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelStatusChanged(SubscriptionObjectType, ChannelBase):
    class Meta:
        root_type = "Channel"
        enable_dry_run = True
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


class OrderCreated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new order is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderUpdated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when order is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderConfirmed(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when order is confirmed." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderFullyPaid(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when order is fully paid." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderFulfilled(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when order is fulfilled." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderCancelled(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when order is canceled." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderMetadataUpdated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when order metadata is updated." + ADDED_IN_38 + PREVIEW_FEATURE
        )


class DraftOrderCreated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new draft order is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class DraftOrderUpdated(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when draft order is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class DraftOrderDeleted(SubscriptionObjectType, OrderBase):
    class Meta:
        root_type = "Order"
        enable_dry_run = True
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


class GiftCardCreated(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new gift card is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardUpdated(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when gift card is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardDeleted(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when gift card is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardStatusChanged(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when gift card status has changed."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class GiftCardMetadataUpdated(SubscriptionObjectType, GiftCardBase):
    class Meta:
        root_type = "GiftCard"
        enable_dry_run = True
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


class MenuCreated(SubscriptionObjectType, MenuBase):
    class Meta:
        root_type = "Menu"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new menu is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuUpdated(SubscriptionObjectType, MenuBase):
    class Meta:
        root_type = "Menu"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when menu is updated." + ADDED_IN_34 + PREVIEW_FEATURE


class MenuDeleted(SubscriptionObjectType, MenuBase):
    class Meta:
        root_type = "Menu"
        enable_dry_run = True
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


class MenuItemCreated(SubscriptionObjectType, MenuItemBase):
    class Meta:
        root_type = "MenuItem"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new menu item is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuItemUpdated(SubscriptionObjectType, MenuItemBase):
    class Meta:
        root_type = "MenuItem"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when menu item is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuItemDeleted(SubscriptionObjectType, MenuItemBase):
    class Meta:
        root_type = "MenuItem"
        enable_dry_run = True
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


class ProductCreated(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new product is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ProductUpdated(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when product is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ProductDeleted(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when product is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ProductMetadataUpdated(SubscriptionObjectType, ProductBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
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


class ProductVariantCreated(SubscriptionObjectType, ProductVariantBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new product variant is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantUpdated(SubscriptionObjectType, ProductVariantBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when product variant is updated."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantDeleted(SubscriptionObjectType, ProductVariantBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when product variant is deleted."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantMetadataUpdated(SubscriptionObjectType, ProductVariantBase):
    class Meta:
        root_type = "Product"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when product variant metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class ProductVariantOutOfStock(SubscriptionObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        root_type = "Stock"
        enable_dry_run = True
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


class ProductVariantBackInStock(SubscriptionObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        root_type = "Stock"
        enable_dry_run = True
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


class ProductVariantStockUpdated(SubscriptionObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when product variant stock is updated."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        )

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
            "Event sent when new sale is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class SaleUpdated(SubscriptionObjectType, SaleBase):
    class Meta:
        root_type = "Sale"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when sale is updated." + ADDED_IN_32 + PREVIEW_FEATURE


class SaleDeleted(SubscriptionObjectType, SaleBase):
    class Meta:
        root_type = "Sale"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when sale is deleted." + ADDED_IN_32 + PREVIEW_FEATURE


class SaleToggle(SubscriptionObjectType, SaleBase):
    sale = graphene.Field(
        "saleor.graphql.discount.types.Sale",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The sale the event relates to." + ADDED_IN_35 + PREVIEW_FEATURE,
    )

    class Meta:
        root_type = "Sale"
        enable_dry_run = True
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
        description = (
            "Event sent when invoice is requested." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class InvoiceDeleted(SubscriptionObjectType, InvoiceBase):
    class Meta:
        root_type = "Invoice"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when invoice is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class InvoiceSent(SubscriptionObjectType, InvoiceBase):
    class Meta:
        root_type = "Invoice"
        enable_dry_run = True
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


class FulfillmentCreated(SubscriptionObjectType, FulfillmentBase):
    class Meta:
        root_type = "Fulfillment"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new fulfillment is created."
            + ADDED_IN_34
            + PREVIEW_FEATURE
        )


class FulfillmentCanceled(SubscriptionObjectType, FulfillmentBase):
    class Meta:
        root_type = "Fulfillment"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when fulfillment is canceled." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class FulfillmentApproved(SubscriptionObjectType, FulfillmentBase):
    class Meta:
        root_type = "Fulfillment"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when fulfillment is approved." + ADDED_IN_37 + PREVIEW_FEATURE
        )


class FulfillmentMetadataUpdated(SubscriptionObjectType, FulfillmentBase):
    class Meta:
        root_type = "Fulfillment"
        enable_dry_run = True
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


class CustomerCreated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new customer user is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class CustomerUpdated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when customer user is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CustomerMetadataUpdated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
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


class CollectionCreated(SubscriptionObjectType, CollectionBase):
    class Meta:
        root_type = "Collection"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new collection is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionUpdated(SubscriptionObjectType, CollectionBase):
    class Meta:
        root_type = "Collection"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when collection is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionDeleted(SubscriptionObjectType, CollectionBase):
    class Meta:
        root_type = "Collection"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when collection is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionMetadataUpdated(SubscriptionObjectType, CollectionBase):
    class Meta:
        root_type = "Collection"
        enable_dry_run = True
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


class CheckoutCreated(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = "Checkout"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new checkout is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CheckoutUpdated(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = "Checkout"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when checkout is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CheckoutMetadataUpdated(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = "Checkout"
        enable_dry_run = True
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


class PageCreated(SubscriptionObjectType, PageBase):
    class Meta:
        root_type = "Page"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new page is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class PageUpdated(SubscriptionObjectType, PageBase):
    class Meta:
        root_type = "Page"
        enable_dry_run = True
        interfaces = (Event,)
        description = "Event sent when page is updated." + ADDED_IN_32 + PREVIEW_FEATURE


class PageDeleted(SubscriptionObjectType, PageBase):
    class Meta:
        root_type = "Page"
        enable_dry_run = True
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


class PageTypeCreated(SubscriptionObjectType, PageTypeBase):
    class Meta:
        root_type = "PageType"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new page type is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class PageTypeUpdated(SubscriptionObjectType, PageTypeBase):
    class Meta:
        root_type = "PageType"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when page type is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class PageTypeDeleted(SubscriptionObjectType, PageTypeBase):
    class Meta:
        root_type = "PageType"
        enable_dry_run = True
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


class PermissionGroupCreated(SubscriptionObjectType, PermissionGroupBase):
    class Meta:
        root_type = "Group"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new permission group is created."
            + ADDED_IN_36
            + PREVIEW_FEATURE
        )


class PermissionGroupUpdated(SubscriptionObjectType, PermissionGroupBase):
    class Meta:
        root_type = "Group"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when permission group is updated."
            + ADDED_IN_36
            + PREVIEW_FEATURE
        )


class PermissionGroupDeleted(SubscriptionObjectType, PermissionGroupBase):
    class Meta:
        root_type = "Group"
        enable_dry_run = True
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


class ShippingPriceCreated(SubscriptionObjectType, ShippingPriceBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when new shipping price is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ShippingPriceUpdated(SubscriptionObjectType, ShippingPriceBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when shipping price is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ShippingPriceDeleted(SubscriptionObjectType, ShippingPriceBase):
    class Meta:
        root_type = None
        enable_dry_run = False
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


class ShippingZoneCreated(SubscriptionObjectType, ShippingZoneBase):
    class Meta:
        root_type = "ShippingZone"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new shipping zone is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ShippingZoneUpdated(SubscriptionObjectType, ShippingZoneBase):
    class Meta:
        root_type = "ShippingZone"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when shipping zone is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ShippingZoneDeleted(SubscriptionObjectType, ShippingZoneBase):
    class Meta:
        root_type = "ShippingZone"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when shipping zone is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ShippingZoneMetadataUpdated(SubscriptionObjectType, ShippingZoneBase):
    class Meta:
        root_type = "ShippingZone"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when shipping zone metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class StaffCreated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new staff user is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class StaffUpdated(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when staff user is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class StaffDeleted(SubscriptionObjectType, UserBase):
    class Meta:
        root_type = "User"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when staff user is deleted." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class TransactionAction(SubscriptionObjectType, AbstractType):
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


class TransactionActionRequest(SubscriptionObjectType):
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
        root_type = None
        enable_dry_run = False
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


class TransactionItemMetadataUpdated(SubscriptionObjectType):
    transaction = graphene.Field(
        TransactionItem,
        description="Look up a transaction." + PREVIEW_FEATURE,
    )

    class Meta:
        root_type = "TransactionItem"
        enable_dry_run = True
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


class TranslationCreated(SubscriptionObjectType, TranslationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Event sent when new translation is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class TranslationUpdated(SubscriptionObjectType, TranslationBase):
    class Meta:
        root_type = None
        enable_dry_run = False
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


class VoucherCreated(SubscriptionObjectType, VoucherBase):
    class Meta:
        root_type = "Voucher"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new voucher is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class VoucherUpdated(SubscriptionObjectType, VoucherBase):
    class Meta:
        root_type = "Voucher"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when voucher is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class VoucherDeleted(SubscriptionObjectType, VoucherBase):
    class Meta:
        root_type = "Voucher"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when voucher is deleted." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class VoucherMetadataUpdated(SubscriptionObjectType, VoucherBase):
    class Meta:
        root_type = "Voucher"
        enable_dry_run = True
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


class PaymentAuthorize(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Authorize payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentCaptureEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Capture payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentRefundEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Refund payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentVoidEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Void payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentConfirmEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Confirm payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentProcessEvent(SubscriptionObjectType, PaymentBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "Process payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentListGateways(SubscriptionObjectType, CheckoutBase):
    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "List payment gateways." + ADDED_IN_36 + PREVIEW_FEATURE


class ShippingListMethodsForCheckout(SubscriptionObjectType, CheckoutBase):
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
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "List shipping methods for checkout." + ADDED_IN_36 + PREVIEW_FEATURE
        )


class CalculateTaxes(SubscriptionObjectType):
    tax_base = graphene.Field(
        "saleor.graphql.core.types.taxes.TaxableObject", required=True
    )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Synchronous webhook for calculating checkout/order taxes."
            + ADDED_IN_37
            + PREVIEW_FEATURE
        )

    def resolve_tax_base(root, _info: ResolveInfo):
        _, tax_base = root
        return tax_base


class CheckoutFilterShippingMethods(SubscriptionObjectType, CheckoutBase):
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
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = (
            "Filter shipping methods for checkout." + ADDED_IN_36 + PREVIEW_FEATURE
        )


class OrderFilterShippingMethods(SubscriptionObjectType, OrderBase):
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
        root_type = None
        enable_dry_run = False
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


class WarehouseCreated(SubscriptionObjectType, WarehouseBase):
    class Meta:
        root_type = "Warehouse"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when new warehouse is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseUpdated(SubscriptionObjectType, WarehouseBase):
    class Meta:
        root_type = "Warehouse"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when warehouse is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseDeleted(SubscriptionObjectType, WarehouseBase):
    class Meta:
        root_type = "Warehouse"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when warehouse is deleted." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseMetadataUpdated(SubscriptionObjectType, WarehouseBase):
    class Meta:
        root_type = "Warehouse"
        enable_dry_run = True
        interfaces = (Event,)
        description = (
            "Event sent when warehouse metadata is updated."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )


class Subscription(SubscriptionObjectType):
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
    WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED: ProductVariantStockUpdated,
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
