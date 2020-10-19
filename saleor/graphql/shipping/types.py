import graphene
from graphene import relay

from ...core.permissions import ShippingPermissions
from ...core.weight import convert_weight_to_default_weight_unit
from ...shipping import models
from ..channel.types import ChannelContext, ChannelContextType
from ..core.connection import CountableDjangoObjectType
from ..core.types import CountryDisplay, Money, MoneyRange
from ..decorators import permission_required
from ..shipping.resolvers import resolve_price_range
from ..translations.fields import TranslationField
from ..translations.types import ShippingMethodTranslation
from ..warehouse.types import Warehouse
from .enums import ShippingMethodTypeEnum


class ShippingMethodChannelListing(CountableDjangoObjectType):
    class Meta:
        description = "Represents shipping method channel listing."
        model = models.ShippingMethodChannelListing
        interfaces = [relay.Node]
        only_fields = [
            "id",
            "channel",
            "price",
            "maximum_order_price",
            "minimum_order_price",
        ]


class ShippingMethod(ChannelContextType, CountableDjangoObjectType):
    type = ShippingMethodTypeEnum(description="Type of the shipping method.")
    translation = TranslationField(
        ShippingMethodTranslation,
        type_name="shipping method",
        resolver=ChannelContextType.resolve_translation,
    )
    # TODO: change to channel_listings
    channel_listing = graphene.List(
        graphene.NonNull(ShippingMethodChannelListing),
        description="List of channels available for the method.",
    )
    price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )
    maximum_order_price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )
    minimum_order_price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Shipping method are the methods you'll use to get customer's orders to "
            "them. They are directly exposed to the customers."
        )
        model = models.ShippingMethod
        interfaces = [relay.Node]
        only_fields = [
            "id",
            "maximum_order_weight",
            "minimum_order_weight",
            "name",
        ]

    @staticmethod
    def resolve_price(root: ChannelContext[models.ShippingMethod], *_args):
        # Price field are dynamically generated in available_shipping_methods resolver
        price = getattr(root.node, "price", None)
        if price:
            return price
        # TODO: Add dataloader.
        return root.node.channel_listing.get(channel__slug=root.channel_slug).price

    @staticmethod
    def resolve_maximum_order_price(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        # TODO: Add dataloader.
        return root.node.channel_listing.get(
            channel__slug=root.channel_slug
        ).maximum_order_price

    @staticmethod
    def resolve_minimum_order_price(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        # TODO: Add dataloader.
        return root.node.channel_listing.get(
            channel__slug=root.channel_slug
        ).minimum_order_price

    @staticmethod
    @permission_required(ShippingPermissions.MANAGE_SHIPPING)
    def resolve_channel_listing(root: ChannelContext[models.ShippingMethod], *_args):
        # TODO: Add dataloader.
        return root.node.channel_listing.all()

    @staticmethod
    def resolve_maximum_order_weight(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        return convert_weight_to_default_weight_unit(root.node.maximum_order_weight)

    @staticmethod
    def resolve_minimum_order_weight(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        return convert_weight_to_default_weight_unit(root.node.minimum_order_weight)


class ShippingZone(ChannelContextType, CountableDjangoObjectType):
    price_range = graphene.Field(
        MoneyRange, description="Lowest and highest prices for the shipping."
    )
    countries = graphene.List(
        CountryDisplay, description="List of countries available for the method."
    )
    shipping_methods = graphene.List(
        ShippingMethod,
        description=(
            "List of shipping methods available for orders"
            " shipped to countries within this shipping zone."
        ),
    )
    warehouses = graphene.List(
        Warehouse, description="List of warehouses for shipping zone."
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Represents a shipping zone in the shop. Zones are the concept used only "
            "for grouping shipping methods in the dashboard, and are never exposed to "
            "the customers directly."
        )
        model = models.ShippingZone
        interfaces = [relay.Node]
        only_fields = ["default", "id", "name"]

    @staticmethod
    def resolve_price_range(root: ChannelContext[models.ShippingZone], *_args):
        return resolve_price_range(root.channel_slug)

    @staticmethod
    def resolve_countries(root: ChannelContext[models.ShippingZone], *_args):
        return [
            CountryDisplay(code=country.code, country=country.name)
            for country in root.node.countries
        ]

    @staticmethod
    def resolve_shipping_methods(root: ChannelContext[models.ShippingZone], *_args):
        shipping_methods = [
            ChannelContext(node=shipping, channel_slug=root.channel_slug)
            for shipping in root.node.shipping_methods.all()
        ]
        return shipping_methods

    @staticmethod
    def resolve_warehouses(root: ChannelContext[models.ShippingZone], *_args):
        return root.node.warehouses.all()
