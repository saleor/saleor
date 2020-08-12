import graphene
from graphene import relay

from ...core.permissions import ShippingPermissions
from ...core.weight import convert_weight_to_default_weight_unit
from ...shipping import models
from ..channel.types import ChannelContext, ChannelContextType
from ..core.connection import CountableDjangoObjectType
from ..core.types import CountryDisplay, MoneyRange
from ..decorators import permission_required
from ..translations.fields import TranslationField
from ..translations.types import ShippingMethodTranslation
from ..warehouse.types import Warehouse
from .enums import ShippingMethodTypeEnum


class ShippingMethodChannelListing(CountableDjangoObjectType):
    class Meta:
        description = "Represents shipping method channel listing."
        model = models.ShippingMethodChannelListing
        interfaces = [relay.Node]
        only_fields = ["id", "channel", "price", "min_value", "max_value"]


class ShippingMethod(ChannelContextType, CountableDjangoObjectType):
    type = ShippingMethodTypeEnum(description="Type of the shipping method.")
    translation = TranslationField(
        ShippingMethodTranslation, type_name="shipping method"
    )
    channels = graphene.List(
        ShippingMethodChannelListing,
        description="List of channels available for the method.",
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
            "maximum_order_price",
            "maximum_order_weight",
            "minimum_order_price",
            "minimum_order_weight",
            "name",
            "channels",
            "price",
        ]

    @permission_required(ShippingPermissions.MANAGE_SHIPPING)
    def resolve_channels(root: ChannelContext[models.ShippingMethod], *_args):
        breakpoint()
        return models.ShippingMethodChannelListing.objects.filter(
            shipping_method__id__in=[root.node.pk]
        )

    def resolve_maximum_order_weight(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        return convert_weight_to_default_weight_unit(root.node.maximum_order_weight)

    def resolve_minimum_order_weight(
        root: ChannelContext[models.ShippingMethod], *_args
    ):
        return convert_weight_to_default_weight_unit(root.node.minimum_order_weight)


class ShippingZone(CountableDjangoObjectType):
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
        description = (
            "Represents a shipping zone in the shop. Zones are the concept used only "
            "for grouping shipping methods in the dashboard, and are never exposed to "
            "the customers directly."
        )
        model = models.ShippingZone
        interfaces = [relay.Node]
        only_fields = ["default", "id", "name"]

    @staticmethod
    def resolve_price_range(root: models.ShippingZone, *_args):
        return root.price_range

    @staticmethod
    def resolve_countries(root: models.ShippingZone, *_args):
        return [
            CountryDisplay(code=country.code, country=country.name)
            for country in root.countries
        ]

    @staticmethod
    def resolve_shipping_methods(root: models.ShippingZone, *_args):
        return root.shipping_methods.all()

    @staticmethod
    def resolve_warehouses(root: models.ShippingZone, *_args):
        return root.warehouses.all()
