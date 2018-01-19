import graphene
from graphene import relay
from graphene_django import DjangoConnectionField, DjangoObjectType

from ...shipping.models import ShippingMethod, ShippingMethodCountry
from ..utils import DjangoPkInterface, PriceField


class ShippingMethodType(DjangoObjectType):

    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = ShippingMethod


class ShippingMethodCountryType(DjangoObjectType):
    country_code = graphene.String()
    name = graphene.String()
    price = PriceField()

    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = ShippingMethodCountry

    def resolve_name(self, info):
        return self.shipping_method.name


def resolve_shipping(country_code=None):
    qs = ShippingMethodCountry.objects.select_related('shipping_method')
    if country_code:
        return qs.unique_for_country_code(country_code)
    return qs
