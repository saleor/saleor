import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay

from ...shipping import models
from ..core.connection import CountableDjangoObjectType
from ..core.types import CountryDisplay, MoneyRange
from ..translations.enums import LanguageCodeEnum
from ..translations.resolvers import resolve_translation
from ..translations.types import ShippingMethodTranslation
from .enums import ShippingMethodTypeEnum


class ShippingMethod(CountableDjangoObjectType):
    type = ShippingMethodTypeEnum(description='Type of the shipping method.')
    translation = graphene.Field(
        ShippingMethodTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description='A language code to return the translation for.',
            required=True),
        description=(
            'Returns translated Shipping Method fields '
            'for the given language code.'),
        resolver=resolve_translation)

    class Meta:
        description = """
            Shipping method are the methods you'll use to get
            customer's orders to them.
            They are directly exposed to the customers."""
        model = models.ShippingMethod
        interfaces = [relay.Node]
        only_fields = [
            'id', 'maximum_order_price', 'maximum_order_weight',
            'minimum_order_price', 'minimum_order_weight', 'name', 'price']


class ShippingZone(CountableDjangoObjectType):
    price_range = graphene.Field(
        MoneyRange, description='Lowest and highest prices for the shipping.')
    countries = graphene.List(
        CountryDisplay,
        description='List of countries available for the method.')
    shipping_methods = gql_optimizer.field(
        graphene.List(
            ShippingMethod,
            description=(
                'List of shipping methods available for orders'
                ' shipped to countries within this shipping zone.')),
        model_field='shipping_methods')

    class Meta:
        description = """
            Represents a shipping zone in the shop. Zones are the concept
            used only for grouping shipping methods in the dashboard,
            and are never exposed to the customers directly."""
        model = models.ShippingZone
        interfaces = [relay.Node]
        only_fields = ['default', 'id', 'name']

    def resolve_price_range(self, *_args):
        return self.price_range

    def resolve_countries(self, *_args):
        return [
            CountryDisplay(code=country.code, country=country.name)
            for country in self.countries]

    def resolve_shipping_methods(self, *_args):
        return self.shipping_methods.all()
