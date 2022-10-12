import graphene
from graphene import relay

from ...core.permissions import CheckoutPermissions, ShippingPermissions
from ...core.tracing import traced_resolver
from ...core.weight import convert_weight_to_default_weight_unit
from ...product import models as product_models
from ...shipping import models
from ...shipping.interface import ShippingMethodData
from ..account.enums import CountryCodeEnum
from ..channel import ChannelQsContext
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import (
    Channel,
    ChannelContext,
    ChannelContextType,
    ChannelContextTypeWithMetadata,
    ChannelContextTypeWithMetadataForObjectType,
)
from ..core.connection import CountableConnection, create_connection_slice
from ..core.descriptions import (
    ADDED_IN_36,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
    RICH_CONTENT,
)
from ..core.fields import ConnectionField, JSONString, PermissionsField
from ..core.types import (
    CountryDisplay,
    ModelObjectType,
    Money,
    MoneyRange,
    NonNullList,
    Weight,
)
from ..meta.types import ObjectWithMetadata
from ..shipping.resolvers import resolve_price_range, resolve_shipping_translation
from ..tax.dataloaders import TaxClassByIdLoader
from ..tax.types import TaxClass
from ..translations.fields import TranslationField
from ..translations.types import ShippingMethodTranslation
from ..warehouse.types import Warehouse
from .dataloaders import (
    ChannelsByShippingZoneIdLoader,
    PostalCodeRulesByShippingMethodIdLoader,
    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader,
    ShippingMethodChannelListingByShippingMethodIdLoader,
    ShippingMethodsByShippingZoneIdAndChannelSlugLoader,
    ShippingMethodsByShippingZoneIdLoader,
)
from .enums import PostalCodeRuleInclusionTypeEnum, ShippingMethodTypeEnum


class ShippingMethodChannelListing(ModelObjectType):
    id = graphene.GlobalID(required=True)
    channel = graphene.Field(Channel, required=True)
    maximum_order_price = graphene.Field(Money)
    minimum_order_price = graphene.Field(Money)
    price = graphene.Field(Money)

    class Meta:
        description = "Represents shipping method channel listing."
        model = models.ShippingMethodChannelListing
        interfaces = [relay.Node]

    @staticmethod
    def resolve_channel(root: models.ShippingMethodChannelListing, info):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    def resolve_minimum_order_price(root: models.ShippingMethodChannelListing, info):
        if root.minimum_order_price_amount is None:
            return None
        else:
            return root.minimum_order_price


class ShippingMethodPostalCodeRule(ModelObjectType):
    start = graphene.String(description="Start address range.")
    end = graphene.String(description="End address range.")
    inclusion_type = PostalCodeRuleInclusionTypeEnum(
        description="Inclusion type of the postal code rule."
    )

    class Meta:
        description = "Represents shipping method postal code rule."
        interfaces = [relay.Node]
        model = models.ShippingMethodPostalCodeRule


class ShippingMethodType(ChannelContextTypeWithMetadataForObjectType):
    """Represents internal shipping method managed within Saleor.

    Internal and external (fetched by sync webhooks) shipping methods are later
    represented by `ShippingMethod` objects as part of orders and checkouts.
    """

    id = graphene.ID(required=True, description="Shipping method ID.")
    name = graphene.String(required=True, description="Shipping method name.")
    description = JSONString(description="Shipping method description." + RICH_CONTENT)
    type = ShippingMethodTypeEnum(description="Type of the shipping method.")
    translation = TranslationField(
        ShippingMethodTranslation,
        type_name="shipping method",
        resolver=None,  # Disable default resolver
    )
    channel_listings = PermissionsField(
        NonNullList(ShippingMethodChannelListing),
        description="List of channels available for the method.",
        permissions=[
            ShippingPermissions.MANAGE_SHIPPING,
        ],
    )
    maximum_order_price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )
    minimum_order_price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )
    postal_code_rules = NonNullList(
        ShippingMethodPostalCodeRule,
        description=(
            "Postal code ranges rule of exclusion or inclusion of the shipping method."
        ),
    )
    excluded_products = ConnectionField(
        "saleor.graphql.product.types.products.ProductCountableConnection",
        description="List of excluded products for the shipping method.",
        permissions=[ShippingPermissions.MANAGE_SHIPPING],
    )
    minimum_order_weight = graphene.Field(
        Weight, description="Minimum order weight to use this shipping method."
    )
    maximum_order_weight = graphene.Field(
        Weight, description="Maximum order weight to use this shipping method."
    )
    maximum_delivery_days = graphene.Int(
        description="Maximum number of days for delivery."
    )
    minimum_delivery_days = graphene.Int(
        description="Minimal number of days for delivery."
    )
    tax_class = PermissionsField(
        TaxClass,
        description="Tax class assigned to this shipping method.",
        required=False,
        permissions=[
            CheckoutPermissions.MANAGE_TAXES,
            ShippingPermissions.MANAGE_SHIPPING,
        ],
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Shipping method are the methods you'll use to get customer's orders to "
            "them. They are directly exposed to the customers."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.ShippingMethod

    @staticmethod
    def resolve_id(root: ChannelContext, _info):
        return graphene.Node.to_global_id("ShippingMethodType", root.node.id)

    @staticmethod
    def resolve_maximum_order_price(root: ChannelContext[models.ShippingMethod], info):
        maximum_order_price = getattr(root.node, "maximum_order_price", None)
        if maximum_order_price is not None:
            return maximum_order_price

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
    def resolve_minimum_order_price(root: ChannelContext[models.ShippingMethod], info):
        minimum_order_price = getattr(root.node, "minimum_order_price", None)
        if minimum_order_price is not None:
            return minimum_order_price

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
        root: ChannelContext[models.ShippingMethod], _info
    ):
        return convert_weight_to_default_weight_unit(root.node.maximum_order_weight)

    @staticmethod
    def resolve_postal_code_rules(root: ChannelContext[models.ShippingMethod], info):
        return PostalCodeRulesByShippingMethodIdLoader(info.context).load(root.node.id)

    @staticmethod
    def resolve_minimum_order_weight(
        root: ChannelContext[models.ShippingMethod], _info
    ):
        return convert_weight_to_default_weight_unit(root.node.minimum_order_weight)

    @staticmethod
    def resolve_channel_listings(root: ChannelContext[models.ShippingMethod], info):
        return ShippingMethodChannelListingByShippingMethodIdLoader(info.context).load(
            root.node.id
        )

    @staticmethod
    def resolve_excluded_products(
        root: ChannelContext[models.ShippingMethod], info, **kwargs
    ):
        from ..product.types import ProductCountableConnection

        if not root.node.excluded_products:
            qs = product_models.Product.objects.none()
        else:
            qs = ChannelQsContext(
                qs=root.node.excluded_products.all(), channel_slug=None  # type: ignore
            )

        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

    @staticmethod
    def resolve_tax_class(root: ChannelContext[models.ShippingMethod], info):
        return (
            TaxClassByIdLoader(info.context).load(root.node.tax_class_id)
            if root.node.tax_class_id
            else None
        )


class ShippingZone(ChannelContextTypeWithMetadata, ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    default = graphene.Boolean(required=True)
    price_range = graphene.Field(
        MoneyRange, description="Lowest and highest prices for the shipping."
    )
    countries = NonNullList(
        CountryDisplay,
        description="List of countries available for the method.",
        required=True,
    )
    shipping_methods = NonNullList(
        ShippingMethodType,
        description=(
            "List of shipping methods available for orders"
            " shipped to countries within this shipping zone."
        ),
    )
    warehouses = NonNullList(
        Warehouse,
        description="List of warehouses for shipping zone.",
        required=True,
    )
    channels = NonNullList(
        Channel,
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

    @staticmethod
    @traced_resolver
    def resolve_price_range(root: ChannelContext[models.ShippingZone], _info):
        return resolve_price_range(root.channel_slug)

    @staticmethod
    def resolve_countries(root: ChannelContext[models.ShippingZone], _info):
        return [
            CountryDisplay(code=country.code, country=country.name)
            for country in root.node.countries
        ]

    @staticmethod
    def resolve_shipping_methods(root: ChannelContext[models.ShippingZone], info):
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
    def resolve_warehouses(root: ChannelContext[models.ShippingZone], _info):
        return root.node.warehouses.all()

    @staticmethod
    def resolve_channels(root: ChannelContext[models.ShippingZone], info):
        return ChannelsByShippingZoneIdLoader(info.context).load(root.node.id)


class ShippingMethod(graphene.ObjectType):
    id = graphene.ID(
        required=True, description="Unique ID of ShippingMethod available for Order."
    )
    type = ShippingMethodTypeEnum(
        description="Type of the shipping method.",
        deprecation_reason=DEPRECATED_IN_3X_FIELD,
    )
    name = graphene.String(required=True, description="Shipping method name.")
    description = JSONString(description="Shipping method description." + RICH_CONTENT)
    maximum_delivery_days = graphene.Int(
        description="Maximum delivery days for this shipping method."
    )
    minimum_delivery_days = graphene.Int(
        description="Minimum delivery days for this shipping method."
    )
    maximum_order_weight = graphene.Field(
        Weight,
        description="Maximum order weight for this shipping method.",
        deprecation_reason=DEPRECATED_IN_3X_FIELD,
    )
    minimum_order_weight = graphene.Field(
        Weight,
        description="Minimum order weight for this shipping method.",
        deprecation_reason=DEPRECATED_IN_3X_FIELD,
    )
    translation = TranslationField(
        ShippingMethodTranslation,
        type_name="shipping method",
        resolver=resolve_shipping_translation,
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
            "Shipping methods that can be used as means of shipping "
            "for orders and checkouts."
        )

    @staticmethod
    def resolve_id(root: ShippingMethodData, _info):
        return root.graphql_id

    @staticmethod
    def resolve_maximum_order_weight(root: ShippingMethodData, _info):
        return convert_weight_to_default_weight_unit(root.maximum_order_weight)

    @staticmethod
    def resolve_minimum_order_weight(root: ShippingMethodData, _info):
        return convert_weight_to_default_weight_unit(root.minimum_order_weight)


class ShippingZoneCountableConnection(CountableConnection):
    class Meta:
        node = ShippingZone


class ShippingMethodsPerCountry(graphene.ObjectType):
    country_code = graphene.Field(
        CountryCodeEnum, required=True, description="The country code."
    )
    shipping_methods = NonNullList(
        ShippingMethod, description="List of available shipping methods."
    )

    class Meta:
        description = (
            "List of shipping methods available for the country."
            + ADDED_IN_36
            + PREVIEW_FEATURE
        )
