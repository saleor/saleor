import graphene
from graphene import AbstractType, ObjectType, Union
from rx import Observable

from ...attribute.models import AttributeTranslation, AttributeValueTranslation
from ...core.prices import quantize_price
from ...discount.models import SaleTranslation, VoucherTranslation
from ...menu.models import MenuItemTranslation
from ...page.models import PageTranslation
from ...payment.interface import TransactionActionData
from ...product.models import (
    CategoryTranslation,
    CollectionTranslation,
    ProductTranslation,
    ProductVariantTranslation,
)
from ...shipping.models import ShippingMethodTranslation
from ...webhook.event_types import WebhookEventAsyncType
from ..channel import ChannelContext
from ..core.descriptions import ADDED_IN_32, ADDED_IN_34, PREVIEW_FEATURE
from ..core.scalars import PositiveDecimal
from ..payment.enums import TransactionActionEnum
from ..payment.types import TransactionItem
from ..translations import types as translation_types

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


class AppBase(AbstractType):
    app = graphene.Field(
        "saleor.graphql.app.types.App",
        description="Look up a app." + ADDED_IN_34 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_app(root, _info):
        _, app = root
        return app


class AppCreated(ObjectType, AppBase):
    ...


class AppUpdated(ObjectType, AppBase):
    ...


class AppDeleted(ObjectType, AppBase):
    ...


class AppStatusChanged(ObjectType, AppBase):
    ...


class CategoryBase(AbstractType):
    category = graphene.Field(
        "saleor.graphql.product.types.Category",
        description="Look up a category." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_category(root, info):
        _, category = root
        return category


class CategoryCreated(ObjectType, CategoryBase):
    ...


class CategoryUpdated(ObjectType, CategoryBase):
    ...


class CategoryDeleted(ObjectType, CategoryBase):
    ...


class ChannelBase(AbstractType):
    channel = graphene.Field(
        "saleor.graphql.channel.types.Channel",
        description="Look up a channel." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_channel(root, info):
        _, channel = root
        return channel


class ChannelCreated(ObjectType, ChannelBase):
    ...


class ChannelUpdated(ObjectType, ChannelBase):
    ...


class ChannelDeleted(ObjectType, ChannelBase):
    ...


class ChannelStatusChanged(ObjectType, ChannelBase):
    ...


class OrderBase(AbstractType):
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="Look up an order." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_order(root, info):
        _, order = root
        return order


class OrderCreated(ObjectType, OrderBase):
    ...


class OrderUpdated(ObjectType, OrderBase):
    ...


class OrderConfirmed(ObjectType, OrderBase):
    ...


class OrderFullyPaid(ObjectType, OrderBase):
    ...


class OrderFulfilled(ObjectType, OrderBase):
    ...


class OrderCancelled(ObjectType, OrderBase):
    ...


class DraftOrderCreated(ObjectType, OrderBase):
    ...


class DraftOrderUpdated(ObjectType, OrderBase):
    ...


class DraftOrderDeleted(ObjectType, OrderBase):
    ...


class GiftCardBase(AbstractType):
    gift_card = graphene.Field(
        "saleor.graphql.giftcard.types.GiftCard",
        description="Look up a gift card." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_gift_card(root, info):
        _, gift_card = root
        return gift_card


class GiftCardCreated(ObjectType, GiftCardBase):
    ...


class GiftCardUpdated(ObjectType, GiftCardBase):
    ...


class GiftCardDeleted(ObjectType, GiftCardBase):
    ...


class GiftCardStatusChanged(ObjectType, GiftCardBase):
    ...


class MenuBase(AbstractType):
    menu = graphene.Field(
        "saleor.graphql.menu.types.Menu",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a menu." + ADDED_IN_34 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_menu(root, info, channel=None):
        _, menu = root
        return ChannelContext(node=menu, channel_slug=channel)


class MenuCreated(ObjectType, MenuBase):
    ...


class MenuUpdated(ObjectType, MenuBase):
    ...


class MenuDeleted(ObjectType, MenuBase):
    ...


class MenuItemBase(AbstractType):
    menu_item = graphene.Field(
        "saleor.graphql.menu.types.MenuItem",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a menu item." + ADDED_IN_34 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_menu_item(root, info, channel=None):
        _, menu_item = root
        return ChannelContext(node=menu_item, channel_slug=channel)


class MenuItemCreated(ObjectType, MenuItemBase):
    ...


class MenuItemUpdated(ObjectType, MenuItemBase):
    ...


class MenuItemDeleted(ObjectType, MenuItemBase):
    ...


class ProductBase(AbstractType):
    product = graphene.Field(
        "saleor.graphql.product.types.Product",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a product." + ADDED_IN_32 + PREVIEW_FEATURE,
    )
    category = graphene.Field(
        "saleor.graphql.product.types.products.Category",
        description="Look up a category." + ADDED_IN_32 + PREVIEW_FEATURE,
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
    ...


class ProductUpdated(ObjectType, ProductBase):
    ...


class ProductDeleted(ObjectType, ProductBase):
    ...


class ProductVariantBase(AbstractType):
    product_variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a product variant." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_product_variant(root, _info, channel=None):
        _, variant = root
        return ChannelContext(node=variant, channel_slug=channel)


class ProductVariantCreated(ObjectType, ProductVariantBase):
    ...


class ProductVariantUpdated(ObjectType, ProductVariantBase):
    ...


class ProductVariantDeleted(ObjectType, ProductVariantBase):
    ...


class ProductVariantOutOfStock(ObjectType, ProductVariantBase):
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse",
        description="Look up a warehouse." + ADDED_IN_32 + PREVIEW_FEATURE,
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
        "saleor.graphql.warehouse.types.Warehouse",
        description="Look up a warehouse." + ADDED_IN_32 + PREVIEW_FEATURE,
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
        description="Look up a sale." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_sale(root, info, channel=None):
        _, sale = root
        return ChannelContext(node=sale, channel_slug=channel)


class SaleCreated(ObjectType, SaleBase):
    ...


class SaleUpdated(ObjectType, SaleBase):
    ...


class SaleDeleted(ObjectType, SaleBase):
    ...


class InvoiceBase(AbstractType):
    invoice = graphene.Field(
        "saleor.graphql.invoice.types.Invoice",
        description="Look up an Invoice." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_invoice(root, _info):
        _, invoice = root
        return invoice


class InvoiceRequested(ObjectType, InvoiceBase):
    ...


class InvoiceDeleted(ObjectType, InvoiceBase):
    ...


class InvoiceSent(ObjectType, InvoiceBase):
    ...


class FulfillmentBase(AbstractType):
    fulfillment = graphene.Field(
        "saleor.graphql.order.types.Fulfillment",
        description="Look up a Fulfillment." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_fulfillment(root, _info):
        _, invoice = root
        return invoice


class FulfillmentCreated(ObjectType, FulfillmentBase):
    ...


class FulfillmentCanceled(ObjectType, FulfillmentBase):
    ...


class UserBase(AbstractType):
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="Look up a user." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_user(root, _info):
        _, user = root
        return user


class CustomerCreated(ObjectType, UserBase):
    ...


class CustomerUpdated(ObjectType, UserBase):
    ...


class CollectionBase(AbstractType):
    collection = graphene.Field(
        "saleor.graphql.product.types.products.Collection",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a collection." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_collection(root, _info, channel=None):
        _, collection = root
        return ChannelContext(node=collection, channel_slug=channel)


class CollectionCreated(ObjectType, CollectionBase):
    ...


class CollectionUpdated(ObjectType, CollectionBase):
    ...


class CollectionDeleted(ObjectType, CollectionBase):
    ...


class CheckoutBase(AbstractType):
    checkout = graphene.Field(
        "saleor.graphql.checkout.types.Checkout",
        description="Look up a Checkout." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_checkout(root, _info):
        _, checkout = root
        return checkout


class CheckoutCreated(ObjectType, CheckoutBase):
    ...


class CheckoutUpdated(ObjectType, CheckoutBase):
    ...


class PageBase(AbstractType):
    page = graphene.Field(
        "saleor.graphql.page.types.Page",
        description="Look up a page." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_page(root, _info):
        _, page = root
        return page


class PageCreated(ObjectType, PageBase):
    ...


class PageUpdated(ObjectType, PageBase):
    ...


class PageDeleted(ObjectType, PageBase):
    ...


class ShippingPriceBase(AbstractType):
    shipping_method = graphene.Field(
        "saleor.graphql.shipping.types.ShippingMethodType",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a shipping method." + ADDED_IN_32 + PREVIEW_FEATURE,
    )
    shipping_zone = graphene.Field(
        "saleor.graphql.shipping.types.ShippingZone",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a shipping zone." + ADDED_IN_32 + PREVIEW_FEATURE,
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
    ...


class ShippingPriceUpdated(ObjectType, ShippingPriceBase):
    ...


class ShippingPriceDeleted(ObjectType, ShippingPriceBase):
    ...


class ShippingZoneBase(AbstractType):
    shipping_zone = graphene.Field(
        "saleor.graphql.shipping.types.ShippingZone",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a shipping zone." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_shipping_zone(root, _info, channel=None):
        _, shipping_zone = root
        return ChannelContext(node=shipping_zone, channel_slug=channel)


class ShippingZoneCreated(ObjectType, ShippingZoneBase):
    ...


class ShippingZoneUpdated(ObjectType, ShippingZoneBase):
    ...


class ShippingZoneDeleted(ObjectType, ShippingZoneBase):
    ...


class TransactionAction(ObjectType):
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
        TranslationTypes,
        description="Look up a translation." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_translation(root, _info):
        _, translation = root
        return translation


class TranslationCreated(ObjectType, TranslationBase):
    ...


class TranslationUpdated(ObjectType, TranslationBase):
    ...


class VoucherBase(AbstractType):
    voucher = graphene.Field(
        "saleor.graphql.discount.types.Voucher",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a voucher." + ADDED_IN_34 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_voucher(root, _info):
        _, voucher = root
        return ChannelContext(node=voucher, channel_slug=None)


class VoucherCreated(ObjectType, VoucherBase):
    ...


class VoucherUpdated(ObjectType, VoucherBase):
    ...


class VoucherDeleted(ObjectType, VoucherBase):
    ...


class Event(Union):
    class Meta:
        types = (
            AppCreated,
            AppUpdated,
            AppDeleted,
            AppStatusChanged,
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
            ShippingPriceCreated,
            ShippingPriceUpdated,
            ShippingPriceDeleted,
            ShippingZoneCreated,
            ShippingZoneUpdated,
            ShippingZoneDeleted,
            TransactionActionRequest,
            TranslationCreated,
            TranslationUpdated,
            VoucherCreated,
            VoucherUpdated,
            VoucherDeleted,
        )

    @classmethod
    def get_type(cls, object_type: str):
        types = {
            WebhookEventAsyncType.APP_CREATED: AppCreated,
            WebhookEventAsyncType.APP_UPDATED: AppUpdated,
            WebhookEventAsyncType.APP_DELETED: AppDeleted,
            WebhookEventAsyncType.APP_STATUS_CHANGED: AppStatusChanged,
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
            WebhookEventAsyncType.SHIPPING_PRICE_CREATED: ShippingPriceCreated,
            WebhookEventAsyncType.SHIPPING_PRICE_UPDATED: ShippingPriceUpdated,
            WebhookEventAsyncType.SHIPPING_PRICE_DELETED: ShippingPriceDeleted,
            WebhookEventAsyncType.SHIPPING_ZONE_CREATED: ShippingZoneCreated,
            WebhookEventAsyncType.SHIPPING_ZONE_UPDATED: ShippingZoneUpdated,
            WebhookEventAsyncType.SHIPPING_ZONE_DELETED: ShippingZoneDeleted,
            WebhookEventAsyncType.TRANSACTION_ACTION_REQUEST: TransactionActionRequest,
            WebhookEventAsyncType.TRANSLATION_CREATED: TranslationCreated,
            WebhookEventAsyncType.TRANSLATION_UPDATED: TranslationUpdated,
            WebhookEventAsyncType.VOUCHER_CREATED: VoucherCreated,
            WebhookEventAsyncType.VOUCHER_UPDATED: VoucherUpdated,
            WebhookEventAsyncType.VOUCHER_DELETED: VoucherDeleted,
        }
        return types.get(object_type)

    @classmethod
    def resolve_type(cls, instance, info):
        type_str, _ = instance
        return cls.get_type(type_str)


class Subscription(ObjectType):
    event = graphene.Field(
        Event,
        description="Look up subscription event." + ADDED_IN_32 + PREVIEW_FEATURE,
    )

    @staticmethod
    def resolve_event(root, info):
        return Observable.from_([root])
