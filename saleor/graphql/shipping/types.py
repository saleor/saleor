import graphene
from graphene import relay

from ...shipping import models
from ..core.connection import CountableDjangoObjectType
from ..core.types import CountryDisplay, MoneyRange
from ..translations.fields import TranslationField
from ..translations.types import ShippingMethodTranslation
from ..warehouse.types import Warehouse
from .enums import ShippingMethodTypeEnum


class ShippingMethod(CountableDjangoObjectType):
    type = ShippingMethodTypeEnum(description="Type of the shipping method.")
    translation = TranslationField(
        ShippingMethodTranslation, type_name="shipping method"
    )

    class Meta:
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
            "price",
        ]


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
