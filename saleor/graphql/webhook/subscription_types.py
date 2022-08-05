import graphene
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from graphene import AbstractType, ObjectType, Union
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
from ..core.descriptions import (
    ADDED_IN_32,
    ADDED_IN_34,
    ADDED_IN_35,
    ADDED_IN_36,
    PREVIEW_FEATURE,
)
from ..core.scalars import PositiveDecimal
from ..core.types import NonNullList
from ..payment.enums import TransactionActionEnum
from ..payment.types import TransactionItem
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
    def resolve_type(cls, instance, info):
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
        types = {
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
            WebhookEventAsyncType.DRAFT_ORDER_CREATED: DraftOrderCreated,
            WebhookEventAsyncType.DRAFT_ORDER_UPDATED: DraftOrderUpdated,
            WebhookEventAsyncType.DRAFT_ORDER_DELETED: DraftOrderDeleted,
            WebhookEventAsyncType.PRODUCT_CREATED: ProductCreated,
            WebhookEventAsyncType.PRODUCT_UPDATED: ProductUpdated,
            WebhookEventAsyncType.PRODUCT_DELETED: ProductDeleted,
            WebhookEventAsyncType.PRODUCT_VARIANT_CREATED: ProductVariantCreated,
            WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED: ProductVariantUpdated,
            WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK: (
                ProductVariantOutOfStock
            ),
            WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK: (
                ProductVariantBackInStock
            ),
            WebhookEventAsyncType.PRODUCT_VARIANT_DELETED: ProductVariantDeleted,
            WebhookEventAsyncType.SALE_CREATED: SaleCreated,
            WebhookEventAsyncType.SALE_UPDATED: SaleUpdated,
            WebhookEventAsyncType.SALE_DELETED: SaleDeleted,
            WebhookEventAsyncType.SALE_TOGGLE: SaleToggle,
            WebhookEventAsyncType.INVOICE_REQUESTED: InvoiceRequested,
            WebhookEventAsyncType.INVOICE_DELETED: InvoiceDeleted,
            WebhookEventAsyncType.INVOICE_SENT: InvoiceSent,
            WebhookEventAsyncType.FULFILLMENT_CREATED: FulfillmentCreated,
            WebhookEventAsyncType.FULFILLMENT_CANCELED: FulfillmentCanceled,
            WebhookEventAsyncType.CUSTOMER_CREATED: CustomerCreated,
            WebhookEventAsyncType.CUSTOMER_UPDATED: CustomerUpdated,
            WebhookEventAsyncType.COLLECTION_CREATED: CollectionCreated,
            WebhookEventAsyncType.COLLECTION_UPDATED: CollectionUpdated,
            WebhookEventAsyncType.COLLECTION_DELETED: CollectionDeleted,
            WebhookEventAsyncType.CHECKOUT_CREATED: CheckoutCreated,
            WebhookEventAsyncType.CHECKOUT_UPDATED: CheckoutUpdated,
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
            WebhookEventAsyncType.STAFF_CREATED: StaffCreated,
            WebhookEventAsyncType.STAFF_UPDATED: StaffUpdated,
            WebhookEventAsyncType.STAFF_DELETED: StaffDeleted,
            WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST: TransactionActionRequest,
            WebhookEventAsyncType.TRANSLATION_CREATED: TranslationCreated,
            WebhookEventAsyncType.TRANSLATION_UPDATED: TranslationUpdated,
            WebhookEventAsyncType.VOUCHER_CREATED: VoucherCreated,
            WebhookEventAsyncType.VOUCHER_UPDATED: VoucherUpdated,
            WebhookEventAsyncType.VOUCHER_DELETED: VoucherDeleted,
            WebhookEventAsyncType.WAREHOUSE_CREATED: WarehouseCreated,
            WebhookEventAsyncType.WAREHOUSE_UPDATED: WarehouseUpdated,
            WebhookEventAsyncType.WAREHOUSE_DELETED: WarehouseDeleted,
            WebhookEventSyncType.PAYMENT_AUTHORIZE: PaymentAuthorize,
            WebhookEventSyncType.PAYMENT_CAPTURE: PaymentCaptureEvent,
            WebhookEventSyncType.PAYMENT_REFUND: PaymentRefundEvent,
            WebhookEventSyncType.PAYMENT_VOID: PaymentVoidEvent,
            WebhookEventSyncType.PAYMENT_CONFIRM: PaymentConfirmEvent,
            WebhookEventSyncType.PAYMENT_PROCESS: PaymentProcessEvent,
            WebhookEventSyncType.PAYMENT_LIST_GATEWAYS: PaymentListGateways,
            WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS: (
                OrderFilterShippingMethods
            ),
            WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS: (
                CheckoutFilterShippingMethods
            ),
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT: (
                ShippingListMethodsForCheckout
            ),
        }
        return types.get(object_type)

    @classmethod
    def resolve_type(cls, instance, info):
        type_str, _ = instance
        return cls.get_type(type_str)

    @staticmethod
    def resolve_issued_at(_root, _info):
        return timezone.now()

    @staticmethod
    def resolve_version(_root, _info):
        return __version__

    @staticmethod
    def resolve_recipient(_root, info):
        return info.context.app

    @staticmethod
    def resolve_issuing_principal(_root, info):
        if isinstance(info.context.requestor, AnonymousUser):
            return None
        return info.context.requestor


class AddressBase(AbstractType):
    address = graphene.Field(
        "saleor.graphql.account.types.Address",
        description="The address the event relates to.",
    )

    @staticmethod
    def resolve_address(root, _info):
        _, address = root
        return address


class AddressCreated(ObjectType, AddressBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new address is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AddressUpdated(ObjectType, AddressBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when address is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AddressDeleted(ObjectType, AddressBase):
    class Meta:
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
    def resolve_app(root, _info):
        _, app = root
        return app


class AppInstalled(ObjectType, AppBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new app is installed." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class AppUpdated(ObjectType, AppBase):
    class Meta:
        interfaces = (Event,)
        description = "Event sent when app is updated." + ADDED_IN_34 + PREVIEW_FEATURE


class AppDeleted(ObjectType, AppBase):
    class Meta:
        interfaces = (Event,)
        description = "Event sent when app is deleted." + ADDED_IN_34 + PREVIEW_FEATURE


class AppStatusChanged(ObjectType, AppBase):
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
    def resolve_attribute(root, _info):
        _, attribute = root
        return attribute


class AttributeCreated(ObjectType, AttributeBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new attribute is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AttributeUpdated(ObjectType, AttributeBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when attribute is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class AttributeDeleted(ObjectType, AttributeBase):
    class Meta:
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
    def resolve_attribute_value(root, _info):
        _, attribute = root
        return attribute


class AttributeValueCreated(ObjectType, AttributeValueBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new attribute value is created."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )


class AttributeValueUpdated(ObjectType, AttributeValueBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when attribute value is updated."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )


class AttributeValueDeleted(ObjectType, AttributeValueBase):
    class Meta:
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
    def resolve_category(root, info):
        _, category = root
        return category


class CategoryCreated(ObjectType, CategoryBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new category is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CategoryUpdated(ObjectType, CategoryBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when category is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CategoryDeleted(ObjectType, CategoryBase):
    class Meta:
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
    def resolve_channel(root, info):
        _, channel = root
        return channel


class ChannelCreated(ObjectType, ChannelBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new channel is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelUpdated(ObjectType, ChannelBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when channel is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelDeleted(ObjectType, ChannelBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when channel is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ChannelStatusChanged(ObjectType, ChannelBase):
    class Meta:
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
    def resolve_order(root, info):
        _, order = root
        return order


class OrderCreated(ObjectType, OrderBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new order is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderUpdated(ObjectType, OrderBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when order is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderConfirmed(ObjectType, OrderBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when order is confirmed." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderFullyPaid(ObjectType, OrderBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when order is fully paid." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderFulfilled(ObjectType, OrderBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when order is fulfilled." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class OrderCancelled(ObjectType, OrderBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when order is canceled." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class DraftOrderCreated(ObjectType, OrderBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new draft order is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class DraftOrderUpdated(ObjectType, OrderBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when draft order is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class DraftOrderDeleted(ObjectType, OrderBase):
    class Meta:
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
    def resolve_gift_card(root, info):
        _, gift_card = root
        return gift_card


class GiftCardCreated(ObjectType, GiftCardBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new gift card is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardUpdated(ObjectType, GiftCardBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when gift card is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardDeleted(ObjectType, GiftCardBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when gift card is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class GiftCardStatusChanged(ObjectType, GiftCardBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when gift card status has changed."
            + ADDED_IN_32
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
    def resolve_menu(root, info, channel=None):
        _, menu = root
        return ChannelContext(node=menu, channel_slug=channel)


class MenuCreated(ObjectType, MenuBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new menu is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuUpdated(ObjectType, MenuBase):
    class Meta:
        interfaces = (Event,)
        description = "Event sent when menu is updated." + ADDED_IN_34 + PREVIEW_FEATURE


class MenuDeleted(ObjectType, MenuBase):
    class Meta:
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
    def resolve_menu_item(root, info, channel=None):
        _, menu_item = root
        return ChannelContext(node=menu_item, channel_slug=channel)


class MenuItemCreated(ObjectType, MenuItemBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new menu item is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuItemUpdated(ObjectType, MenuItemBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when menu item is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class MenuItemDeleted(ObjectType, MenuItemBase):
    class Meta:
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
        "saleor.graphql.product.types.products.Category",
        description="The category of the product.",
    )

    @staticmethod
    def resolve_product(root, info, channel=None):
        _, product = root
        return ChannelContext(node=product, channel_slug=channel)

    @staticmethod
    def resolve_category(root, _info):
        _, product = root
        return product.category


class ProductCreated(ObjectType, ProductBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new product is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ProductUpdated(ObjectType, ProductBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when product is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ProductDeleted(ObjectType, ProductBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when product is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
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
    def resolve_product_variant(root, _info, channel=None):
        _, variant = root
        return ChannelContext(node=variant, channel_slug=channel)


class ProductVariantCreated(ObjectType, ProductVariantBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new product variant is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantUpdated(ObjectType, ProductVariantBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when product variant is updated."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantDeleted(ObjectType, ProductVariantBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when product variant is deleted."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ProductVariantOutOfStock(ObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when product variant is out of stock."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )

    @staticmethod
    def resolve_product_variant(root, info, channel=None):
        _, stock = root
        variant = stock.product_variant
        return ChannelContext(node=variant, channel_slug=channel)

    @staticmethod
    def resolve_warehouse(root, _info):
        _, stock = root
        return stock.warehouse


class ProductVariantBackInStock(ObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", description="Look up a warehouse."
    )

    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when product variant is back in stock."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )

    @staticmethod
    def resolve_product_variant(root, _info, channel=None):
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
    def resolve_sale(root, info, channel=None):
        _, sale = root
        return ChannelContext(node=sale, channel_slug=channel)


class SaleCreated(ObjectType, SaleBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new sale is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class SaleUpdated(ObjectType, SaleBase):
    class Meta:
        interfaces = (Event,)
        description = "Event sent when sale is updated." + ADDED_IN_32 + PREVIEW_FEATURE


class SaleDeleted(ObjectType, SaleBase):
    class Meta:
        interfaces = (Event,)
        description = "Event sent when sale is deleted." + ADDED_IN_32 + PREVIEW_FEATURE


class SaleToggle(ObjectType, SaleBase):
    sale = graphene.Field(
        "saleor.graphql.discount.types.Sale",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The sale the event relates to." + ADDED_IN_35 + PREVIEW_FEATURE,
    )

    class Meta:
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

    @staticmethod
    def resolve_invoice(root, _info):
        _, invoice = root
        return invoice


class InvoiceRequested(ObjectType, InvoiceBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when invoice is requested." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class InvoiceDeleted(ObjectType, InvoiceBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when invoice is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class InvoiceSent(ObjectType, InvoiceBase):
    class Meta:
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
    def resolve_fulfillment(root, _info):
        _, fulfillment = root
        return fulfillment

    @staticmethod
    def resolve_order(root, info):
        _, fulfillment = root
        return fulfillment.order


class FulfillmentCreated(ObjectType, FulfillmentBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new fulfillment is created."
            + ADDED_IN_34
            + PREVIEW_FEATURE
        )


class FulfillmentCanceled(ObjectType, FulfillmentBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when fulfillment is canceled." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class UserBase(AbstractType):
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The user the event relates to.",
    )

    @staticmethod
    def resolve_user(root, _info):
        _, user = root
        return user


class CustomerCreated(ObjectType, UserBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new customer user is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class CustomerUpdated(ObjectType, UserBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when customer user is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionBase(AbstractType):
    collection = graphene.Field(
        "saleor.graphql.product.types.products.Collection",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="The collection the event relates to.",
    )

    @staticmethod
    def resolve_collection(root, _info, channel=None):
        _, collection = root
        return ChannelContext(node=collection, channel_slug=channel)


class CollectionCreated(ObjectType, CollectionBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new collection is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionUpdated(ObjectType, CollectionBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when collection is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CollectionDeleted(ObjectType, CollectionBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when collection is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CheckoutBase(AbstractType):
    checkout = graphene.Field(
        "saleor.graphql.checkout.types.Checkout",
        description="The checkout the event relates to.",
    )

    @staticmethod
    def resolve_checkout(root, _info):
        _, checkout = root
        return checkout


class CheckoutCreated(ObjectType, CheckoutBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new checkout is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class CheckoutUpdated(ObjectType, CheckoutBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when checkout is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class PageBase(AbstractType):
    page = graphene.Field(
        "saleor.graphql.page.types.Page", description="The page the event relates to."
    )

    @staticmethod
    def resolve_page(root, _info):
        _, page = root
        return page


class PageCreated(ObjectType, PageBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new page is created." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class PageUpdated(ObjectType, PageBase):
    class Meta:
        interfaces = (Event,)
        description = "Event sent when page is updated." + ADDED_IN_32 + PREVIEW_FEATURE


class PageDeleted(ObjectType, PageBase):
    class Meta:
        interfaces = (Event,)
        description = "Event sent when page is deleted." + ADDED_IN_32 + PREVIEW_FEATURE


class PageTypeBase(AbstractType):
    page_type = graphene.Field(
        "saleor.graphql.page.types.PageType",
        description="The page type the event relates to.",
    )

    @staticmethod
    def resolve_page_type(root, _info):
        _, page_type = root
        return page_type


class PageTypeCreated(ObjectType, PageTypeBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new page type is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class PageTypeUpdated(ObjectType, PageTypeBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when page type is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class PageTypeDeleted(ObjectType, PageTypeBase):
    class Meta:
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
    def resolve_permission_group(root, _info):
        _, permission_group = root
        return permission_group


class PermissionGroupCreated(ObjectType, PermissionGroupBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new permission group is created."
            + ADDED_IN_36
            + PREVIEW_FEATURE
        )


class PermissionGroupUpdated(ObjectType, PermissionGroupBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when permission group is updated."
            + ADDED_IN_36
            + PREVIEW_FEATURE
        )


class PermissionGroupDeleted(ObjectType, PermissionGroupBase):
    class Meta:
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
    def resolve_shipping_method(root, _info, channel=None):
        _, shipping_method = root
        return ChannelContext(node=shipping_method, channel_slug=channel)

    @staticmethod
    def resolve_shipping_zone(root, _info, channel=None):
        _, shipping_method = root
        return ChannelContext(node=shipping_method.shipping_zone, channel_slug=channel)


class ShippingPriceCreated(ObjectType, ShippingPriceBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new shipping price is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ShippingPriceUpdated(ObjectType, ShippingPriceBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when shipping price is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ShippingPriceDeleted(ObjectType, ShippingPriceBase):
    class Meta:
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
    def resolve_shipping_zone(root, _info, channel=None):
        _, shipping_zone = root
        return ChannelContext(node=shipping_zone, channel_slug=channel)


class ShippingZoneCreated(ObjectType, ShippingZoneBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new shipping zone is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class ShippingZoneUpdated(ObjectType, ShippingZoneBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when shipping zone is updated." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class ShippingZoneDeleted(ObjectType, ShippingZoneBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when shipping zone is deleted." + ADDED_IN_32 + PREVIEW_FEATURE
        )


class StaffCreated(ObjectType, UserBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new staff user is created." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class StaffUpdated(ObjectType, UserBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when staff user is updated." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class StaffDeleted(ObjectType, UserBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when staff user is deleted." + ADDED_IN_35 + PREVIEW_FEATURE
        )


class TransactionAction(ObjectType, AbstractType):
    action_type = graphene.Field(
        TransactionActionEnum,
        required=True,
        description="Determines the action type.",
    )
    amount = PositiveDecimal(
        description="Transaction request amount. Null when action type is VOID.",
    )

    @staticmethod
    def resolve_amount(root: TransactionActionData, _info):
        if root.action_value:
            return quantize_price(root.action_value, root.transaction.currency)
        return None


class TransactionActionRequest(ObjectType):
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
        interfaces = (Event,)
        description = (
            "Event sent when transaction action is requested."
            + ADDED_IN_34
            + PREVIEW_FEATURE
        )

    @staticmethod
    def resolve_transaction(root, _info):
        _, transaction_action_data = root
        transaction_action_data: TransactionActionData
        return transaction_action_data.transaction

    @staticmethod
    def resolve_action(root, _info):
        _, transaction_action_data = root
        transaction_action_data: TransactionActionData
        return transaction_action_data


class TranslationTypes(Union):
    class Meta:
        types = tuple(TRANSLATIONS_TYPES_MAP.values())

    @classmethod
    def resolve_type(cls, instance, info):
        instance_type = type(instance)
        if instance_type in TRANSLATIONS_TYPES_MAP:
            return TRANSLATIONS_TYPES_MAP[instance_type]

        return super(TranslationTypes, cls).resolve_type(instance, info)


class TranslationBase(AbstractType):
    translation = graphene.Field(
        TranslationTypes, description="The translation the event relates to."
    )

    @staticmethod
    def resolve_translation(root, _info):
        _, translation = root
        return translation


class TranslationCreated(ObjectType, TranslationBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new translation is created."
            + ADDED_IN_32
            + PREVIEW_FEATURE
        )


class TranslationUpdated(ObjectType, TranslationBase):
    class Meta:
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
    def resolve_voucher(root, _info):
        _, voucher = root
        return ChannelContext(node=voucher, channel_slug=None)


class VoucherCreated(ObjectType, VoucherBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new voucher is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class VoucherUpdated(ObjectType, VoucherBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when voucher is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class VoucherDeleted(ObjectType, VoucherBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when voucher is deleted." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseBase(AbstractType):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse",
        description="The warehouse the event relates to.",
    )

    @staticmethod
    def resolve_warehouse(root, _info):
        _, warehouse = root
        return warehouse


class PaymentBase(AbstractType):
    payment = graphene.Field(
        "saleor.graphql.payment.types.Payment",
        description="Look up a payment.",
    )

    @staticmethod
    def resolve_payment(root, _info):
        _, payment = root
        return payment


class PaymentAuthorize(ObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Authorize payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentCaptureEvent(ObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Capture payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentRefundEvent(ObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Refund payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentVoidEvent(ObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Void payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentConfirmEvent(ObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Confirm payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentProcessEvent(ObjectType, PaymentBase):
    class Meta:
        interfaces = (Event,)
        description = "Process payment." + ADDED_IN_36 + PREVIEW_FEATURE


class PaymentListGateways(ObjectType, CheckoutBase):
    class Meta:
        interfaces = (Event,)
        description = "List payment gateways." + ADDED_IN_36 + PREVIEW_FEATURE


class ShippingListMethodsForCheckout(ObjectType, CheckoutBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36
        + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_shipping_methods(root, info):
        _, checkout = root
        return resolve_shipping_methods_for_checkout(info, checkout)

    class Meta:
        interfaces = (Event,)
        description = (
            "List shipping methods for checkout." + ADDED_IN_36 + PREVIEW_FEATURE
        )


class CheckoutFilterShippingMethods(ObjectType, CheckoutBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36
        + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_shipping_methods(root, info):
        _, checkout = root
        return resolve_shipping_methods_for_checkout(info, checkout)

    class Meta:
        interfaces = (Event,)
        description = (
            "Filter shipping methods for checkout." + ADDED_IN_36 + PREVIEW_FEATURE
        )


class OrderFilterShippingMethods(ObjectType, OrderBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36
        + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_shipping_methods(root, info):
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


class WarehouseCreated(ObjectType, WarehouseBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when new warehouse is created." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseUpdated(ObjectType, WarehouseBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when warehouse is updated." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class WarehouseDeleted(ObjectType, WarehouseBase):
    class Meta:
        interfaces = (Event,)
        description = (
            "Event sent when warehouse is deleted." + ADDED_IN_34 + PREVIEW_FEATURE
        )


class Subscription(ObjectType):
    event = graphene.Field(
        Event,
        description="Look up subscription event." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_event(root, info):
        return Observable.from_([root])


# List of events is created because `Event` type was change from `Union` to `Interface`
# so all subscription events types need to be added manually to `Schema`.

SUBSCRIPTION_EVENTS_TYPES = [
    AddressCreated,
    AddressUpdated,
    AddressDeleted,
    AppInstalled,
    AppUpdated,
    AppDeleted,
    AppStatusChanged,
    AttributeCreated,
    AttributeUpdated,
    AttributeDeleted,
    AttributeValueCreated,
    AttributeValueUpdated,
    AttributeValueDeleted,
    CategoryCreated,
    CategoryUpdated,
    CategoryDeleted,
    ChannelCreated,
    ChannelUpdated,
    ChannelDeleted,
    ChannelStatusChanged,
    GiftCardCreated,
    GiftCardUpdated,
    GiftCardDeleted,
    GiftCardStatusChanged,
    MenuCreated,
    MenuUpdated,
    MenuDeleted,
    MenuItemCreated,
    MenuItemUpdated,
    MenuItemDeleted,
    OrderCreated,
    OrderUpdated,
    OrderConfirmed,
    OrderFullyPaid,
    OrderCancelled,
    OrderFulfilled,
    DraftOrderCreated,
    DraftOrderUpdated,
    DraftOrderDeleted,
    ProductCreated,
    ProductUpdated,
    ProductDeleted,
    ProductVariantCreated,
    ProductVariantUpdated,
    ProductVariantOutOfStock,
    ProductVariantBackInStock,
    ProductVariantDeleted,
    SaleCreated,
    SaleUpdated,
    SaleDeleted,
    SaleToggle,
    InvoiceRequested,
    InvoiceDeleted,
    InvoiceSent,
    FulfillmentCreated,
    FulfillmentCanceled,
    CustomerCreated,
    CustomerUpdated,
    CollectionCreated,
    CollectionUpdated,
    CollectionDeleted,
    CheckoutCreated,
    CheckoutUpdated,
    PageCreated,
    PageUpdated,
    PageDeleted,
    PageTypeCreated,
    PageTypeUpdated,
    PageTypeDeleted,
    PermissionGroupCreated,
    PermissionGroupUpdated,
    PermissionGroupDeleted,
    ShippingPriceCreated,
    ShippingPriceUpdated,
    ShippingPriceDeleted,
    ShippingZoneCreated,
    ShippingZoneUpdated,
    ShippingZoneDeleted,
    StaffCreated,
    StaffUpdated,
    StaffDeleted,
    TransactionActionRequest,
    TranslationCreated,
    TranslationUpdated,
    VoucherCreated,
    VoucherUpdated,
    VoucherDeleted,
    WarehouseCreated,
    WarehouseUpdated,
    WarehouseDeleted,
    PaymentAuthorize,
    PaymentCaptureEvent,
    PaymentRefundEvent,
    PaymentVoidEvent,
    PaymentConfirmEvent,
    PaymentProcessEvent,
    PaymentListGateways,
    OrderFilterShippingMethods,
    CheckoutFilterShippingMethods,
    ShippingListMethodsForCheckout,
]
