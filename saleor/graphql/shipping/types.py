import graphene
from graphene import relay

from ...core.permissions import ShippingPermissions
from ...core.tracing import traced_resolver
from ...core.weight import convert_weight_to_default_weight_unit
from ...shipping import models
from ..channel import ChannelQsContext
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import (
    Channel,
    ChannelContext,
    ChannelContextType,
    ChannelContextTypeWithMetadata,
    MetadataMixin,
)
from ..core.connection import CountableDjangoObjectType
from ..core.fields import ChannelContextFilterConnectionField
from ..core.types import CountryDisplay, Money, MoneyRange, Weight
from ..decorators import permission_required
from ..meta.types import ObjectWithMetadata
from ..shipping.resolvers import (
    resolve_price_range,
    resolve_shipping_maximum_order_price,
)
from ..translations.fields import TranslationField
from ..translations.types import ShippingMethodTranslation
from ..warehouse.types import Warehouse
from .dataloaders import (
    ChannelsByShippingZoneIdLoader,
    PostalCodeRulesByShippingMethodIdLoader,
    ShippingMethodChannelListingByShippingMethodIdLoader,
    ShippingMethodsByShippingZoneIdAndChannelSlugLoader,
    ShippingMethodsByShippingZoneIdLoader,
)
from .enums import PostalCodeRuleInclusionTypeEnum, ShippingMethodTypeEnum
from .resolvers import resolve_shipping_minimum_order_price, resolve_shipping_price


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


class ShippingMethodPostalCodeRule(CountableDjangoObjectType):
    start = graphene.String(description="Start address range.")
    end = graphene.String(description="End address range.")
    inclusion_type = PostalCodeRuleInclusionTypeEnum(
        description="Inclusion type of the postal code rule."
    )

    class Meta:
        description = "Represents shipping method postal code rule."
        interfaces = [relay.Node]
        model = models.ShippingMethodPostalCodeRule
        only_fields = [
            "start",
            "end",
            "inclusion_type",
        ]


class ShippingMethodType(ChannelContextTypeWithMetadata, CountableDjangoObjectType):
    """An internal representation of a shipping method used in private API.

    Used to manage and configure available shipping methods.
    """

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
    postal_code_rules = graphene.List(
        ShippingMethodPostalCodeRule,
        description=(
            "Postal code ranges rule of exclusion or inclusion of the shipping method."
        ),
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
            "description",
        ]

    @staticmethod
    def resolve_maximum_order_price(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        return resolve_shipping_maximum_order_price(root, info, **_kwargs)

    @staticmethod
    def resolve_minimum_order_price(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        return resolve_shipping_minimum_order_price(root, info, **_kwargs)

    @staticmethod
    def resolve_maximum_order_weight(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        return convert_weight_to_default_weight_unit(root.node.maximum_order_weight)

    @staticmethod
    def resolve_postal_code_rules(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        return PostalCodeRulesByShippingMethodIdLoader(info.context).load(root.node.id)

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
        ShippingMethodType,
        description=(
            "List of shipping methods available for orders"
            " shipped to countries within this shipping zone."
        ),
    )
    warehouses = graphene.List(
        graphene.NonNull(Warehouse),
        description="List of warehouses for shipping zone.",
        required=True,
    )
    channels = graphene.List(
        graphene.NonNull(Channel),
        description="List of channels for shipping zone.",
        required=True,
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
    @traced_resolver
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

    @staticmethod
    def resolve_channels(root: ChannelContext[models.ShippingZone], info, **_kwargs):
        return ChannelsByShippingZoneIdLoader(info.context).load(root.node.id)


class ShippingMethod(ChannelContextType, MetadataMixin):
    id = graphene.ID(
        required=True, description="Unique ID of ShippingMethod available for Order."
    )
    type = ShippingMethodTypeEnum(
        description="Type of the shipping method.",
        deprecation_reason="This field will be removed in Saleor 4.0.",
    )

    name = graphene.String(required=True, description="Shipping method name.")
    description = graphene.JSONString(description="Shipping method description (JSON).")
    maximum_delivery_days = graphene.Int(
        description="Maximum delivery days for this shipping method."
    )
    minimum_delivery_days = graphene.Int(
        description="Minimum delivery days for this shipping method."
    )
    maximum_order_weight = graphene.Field(
        Weight,
        description="Maximum order weight for this shipping method.",
        deprecation_reason="This field will be removed in Saleor 4.0.",
    )
    minimum_order_weight = graphene.Field(
        Weight,
        description="Minimum order weight for this shipping method.",
        deprecation_reason="This field will be removed in Saleor 4.0.",
    )
    translation = TranslationField(
        ShippingMethodTranslation,
        type_name="shipping method",
        resolver=ChannelContextType.resolve_translation,
    )
    price = graphene.Field(
        Money, required=True, description="The price of selected shipping method."
    )
    maximum_order_price = graphene.Field(
        Money, description="Maximum order price for this shipping method."
    )
    minimum_order_price = graphene.Field(
        Money, description="Minimal order price for this shipping method."
    )
    active = graphene.Boolean(
        required=True,
        description="Describes if this shipping method is active and can be selected.",
    )
    message = graphene.String(description="Message connected to this shipping method.")

    class Meta:
        interfaces = [relay.Node, ObjectWithMetadata]
        description = (
            (
                "Shipping methods that can be used as means of shipping"
                "for orders and checkouts."
            ),
        )

    @staticmethod
    def resolve_type(root: ChannelContext[models.ShippingMethod], info, **_kwargs):
        return root.node.type

    @staticmethod
    def resolve_minimum_order_price(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        return resolve_shipping_minimum_order_price(root, info, **_kwargs)

    @staticmethod
    def resolve_maximum_order_price(
        root: ChannelContext[models.ShippingMethod], info, **_kwargs
    ):
        return resolve_shipping_maximum_order_price(root, info, **_kwargs)

    @staticmethod
    def resolve_price(root: ChannelContext[models.ShippingMethod], info, **_kwargs):
        # Price field are dynamically generated in available_shipping_methods resolver
        return resolve_shipping_price(root, info, **_kwargs)

    @staticmethod
    def resolve_name(root: ChannelContext[models.ShippingMethod], info, **kwargs):
        return root.node.name

    @staticmethod
    def resolve_id(root: ChannelContext, _info):
        return graphene.Node.to_global_id("ShippingMethod", root.node.id)

    @staticmethod
    def resolve_active(root: ChannelContext, _info):
        # Currently selected shipping method is not validated
        # with webhooks on every single API call
        if not hasattr(root.node, "active"):
            return True
        return root.node.active

    @staticmethod
    def resolve_message(root: ChannelContext, _info):
        # Currently selected shipping method is not validated
        # with webhooks on every single API call
        return getattr(root.node, "message", "")

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

    @staticmethod
    def resolve_description(root: ChannelContext[models.ShippingMethod], *_args):
        return root.node.description
