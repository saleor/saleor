import graphene
from graphene import relay
from graphene_django import DjangoConnectionField, DjangoObjectType

from ...shipping.models import ShippingMethod, ShippingMethodCountry
from ..utils import DjangoPkInterface


class ShippingMethodCountryType(DjangoObjectType):
    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = ShippingMethodCountry


class ShippingMethodType(DjangoObjectType):
    price_per_country = DjangoConnectionField(ShippingMethodCountryType)

    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = ShippingMethod


def resolve_shipping():
    return ShippingMethod.objects.all()
