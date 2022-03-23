import graphene
from graphene import AbstractType, ObjectType, Union
from rx import Observable

from ...webhook.event_types import WebhookEventAsyncType
from ..channel import ChannelContext


class OrderBase(AbstractType):
    order = graphene.Field("saleor.graphql.order.types.Order")

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


class ProductBase(AbstractType):
    product = graphene.Field(
        "saleor.graphql.product.types.Product",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a product.",
    )
    category = graphene.Field(
        "saleor.graphql.product.types.products.Category",
        description="Look up a category.",
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
        description="Look up a product variant.",
    )

    @staticmethod
    def resolve_product_variant(root, info, channel=None):
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
        description="Look up a warehouse.",
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
        description="Look up a warehouse.",
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


class SaleBase(AbstractType):
    sale = graphene.Field(
        "saleor.graphql.discount.types.Sale",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a sale.",
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
        description="Look up an Invoice.",
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
        description="Look up a Fulfillment.",
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
        description="Look up a user.",
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
        description="Look up a collection.",
    )

    @staticmethod
    def resolve_collection(root, info, channel=None):
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
        description="Look up a Checkout.",
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
        description="Look up a page.",
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


class Event(Union):
    class Meta:
        types = (
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
        )

    @classmethod
    def get_type(cls, object_type: str):
        types = {
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
            WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK: ProductVariantOutOfStock,  # noqa
            WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK: ProductVariantBackInStock,  # noqa
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
        }
        return types.get(object_type)

    @classmethod
    def resolve_type(cls, instance, info):
        type_str, _ = instance
        return cls.get_type(type_str)


class Subscription(ObjectType):
    event = graphene.Field(Event)

    @staticmethod
    def resolve_event(root, info):
        return Observable.from_([root])
