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


class ProductBase(AbstractType):
    product = graphene.Field(
        "saleor.graphql.product.types.Product",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a product.",
    )

    @staticmethod
    def resolve_product(root, info, channel=None):
        _, product = root
        return ChannelContext(node=product, channel_slug=channel)


class ProductCreated(ObjectType, ProductBase):
    ...


class ProductUpdated(ObjectType, ProductBase):
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


class Event(Union):
    class Meta:
        types = (
            OrderCreated,
            OrderUpdated,
            OrderConfirmed,
            OrderFullyPaid,
            ProductCreated,
            ProductUpdated,
            ProductVariantCreated,
            ProductVariantUpdated,
            ProductVariantOutOfStock,
            ProductVariantBackInStock,
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
            WebhookEventAsyncType.PRODUCT_CREATED: ProductCreated,
            WebhookEventAsyncType.PRODUCT_UPDATED: ProductUpdated,
            WebhookEventAsyncType.PRODUCT_VARIANT_CREATED: ProductVariantCreated,
            WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED: ProductVariantUpdated,
            WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK: ProductVariantOutOfStock,
            WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK: ProductVariantBackInStock,
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
