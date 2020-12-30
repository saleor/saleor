import graphene
from graphene import relay

from ...core.permissions import ShippingPermissions
from ...core.weight import convert_weight_to_default_weight_unit
from ...shipping import models
from ..channel import ChannelQsContext
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import (
    ChannelContext,
    ChannelContextType,
    ChannelContextTypeWithMetadata,
)
from ..core.connection import CountableDjangoObjectType
from ..core.fields import ChannelContextFilterConnectionField
from ..core.types import CountryDisplay, Money, MoneyRange
from ..decorators import permission_required
from ..meta.types import ObjectWithMetadata
from ..shipping.resolvers import resolve_price_range
from ..translations.fields import TranslationField
from ..translations.types import ShippingMethodTranslation
from ..warehouse.types import Warehouse
from .dataloaders import (
    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader,
    ShippingMethodChannelListingByShippingMethodIdLoader,
    ShippingMethodsByShippingZoneIdAndChannelSlugLoader,
    ShippingMethodsByShippingZoneIdLoader,
    ZipCodeRulesByShippingMethodIdLoader,
)
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

    @staticmethod
    def resolve_channel(root: models.ShippingMethodChannelListing, info, **_kwargs):
        return ChannelByIdLoader(info.context).load(root.channel_id)


class ShippingMethodZipCodeRule(CountableDjangoObjectType):
    start = graphene.String(description="Start address range.")
    end = graphene.String(description="End address range.")

    class Meta:
        description = "Represents shipping method zip code."
        interfaces = [relay.Node]
        model = models.ShippingMethodZipCodeRule
        only_fields = [
            "start",
            "end",
        ]


class ShippingMethod(ChannelContextTypeWithMetadata, CountableDjangoObjectType):
    type = ShippingMethodTypeEnum(description="Type of the shipping method.")
    translation = TranslationField(
        ShippingMethodTranslation,
        type_name="shipping method",
        resolver=ChannelContextType.resolve_translation,
    )
    channel_listings = graphene.List(
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
    zip_code_rules = graphene.List(
        ShippingMethodZipCodeRule,
        description="Zip code exclude range of the shipping method.",
    )
    excluded_products = ChannelContextFilterConnectionField(
        "saleor.graphql.product.types.products.Product",
        description="List of excluded products for the shipping method.",
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Shipping method are the methods you'll use to get customer's orders to "
            "them. They are directly exposed to the customers."
        )
        model = models.ShippingMethod
        interfaces = [relay.Node, ObjectWithMetadata]
        only_fields = [
            "id",
            "maximum_order_weight",
            "minimum_order_weight",
            "maximum_delivery_days",
            "minimum_delivery_days",
            "name",
        ]

    @staticmethod
    def resolve_price(root: ChannelContext[models.ShippingMethod], info, **_kwargs):
        # Price field are dynamically generated in available_shipping_methods resolver
        price = getattr(root.node, "price", None)
        if price:
            return price

        if not root.channel_slug:
            return None

        return (
            ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(
                info.context
            )
            .load((root.node.id, root.channel_slug))
            .then(lambda channel_listing: channel_listing.price)
        )

    @staticmethod
    def resolve_maximum_order_price(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        if not root.channel_slug:
            return None

        return (
            ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(
                info.context
            )
            .load((root.node.id, root.channel_slug))
            .then(lambda channel_listing: channel_listing.maximum_order_price)
        )

    @staticmethod
    def resolve_minimum_order_price(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        if not root.channel_slug:
            return None

        return (
            ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(
                info.context
            )
            .load((root.node.id, root.channel_slug))
            .then(lambda channel_listing: channel_listing.minimum_order_price)
        )

    @staticmethod
    def resolve_maximum_order_weight(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        return convert_weight_to_default_weight_unit(root.node.maximum_order_weight)

    @staticmethod
    def resolve_zip_code_rules(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        return ZipCodeRulesByShippingMethodIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_minimum_order_weight(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        return convert_weight_to_default_weight_unit(root.node.minimum_order_weight)

    @staticmethod
    @permission_required(ShippingPermissions.MANAGE_SHIPPING)
    def resolve_channel_listings(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        return ShippingMethodChannelListingByShippingMethodIdLoader(info.context).load(
            root.node.id
        )

    @staticmethod
    @permission_required(ShippingPermissions.MANAGE_SHIPPING)
    def resolve_excluded_products(
        root: ChannelContext[models.ShippingMethod], _info, **_kwargs
    ):
        return ChannelQsContext(qs=root.node.excluded_products.all(), channel_slug=None)


class ShippingZone(ChannelContextTypeWithMetadata, CountableDjangoObjectType):
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
    description = graphene.String(description="Description of a shipping zone.")

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Represents a shipping zone in the shop. Zones are the concept used only "
            "for grouping shipping methods in the dashboard, and are never exposed to "
            "the customers directly."
        )
        model = models.ShippingZone
        interfaces = [relay.Node, ObjectWithMetadata]
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
    def resolve_shipping_methods(
        root: ChannelContext[models.ShippingZone], info, **_kwargs
    ):
        def wrap_shipping_method_with_channel_context(shipping_methods):
            shipping_methods = [
                ChannelContext(node=shipping, channel_slug=root.channel_slug)
                for shipping in shipping_methods
            ]
            return shipping_methods

        channel_slug = root.channel_slug
        if channel_slug:
            return (
                ShippingMethodsByShippingZoneIdAndChannelSlugLoader(info.context)
                .load((root.node.id, channel_slug))
                .then(wrap_shipping_method_with_channel_context)
            )

        return (
            ShippingMethodsByShippingZoneIdLoader(info.context)
            .load(root.node.id)
            .then(wrap_shipping_method_with_channel_context)
        )

    @staticmethod
    def resolve_warehouses(root: ChannelContext[models.ShippingZone], *_args):
        return root.node.warehouses.all()
