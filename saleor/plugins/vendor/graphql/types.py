import graphene
from graphene import relay

from saleor.graphql.core.connection import CountableDjangoObjectType
from saleor.plugins.vendor.models import Vendor as VendorModel


class Vendor(CountableDjangoObjectType):
    class Meta:
        model = VendorModel
        filter_fields = ["id", "name", "country"]
        interfaces = (graphene.relay.Node,)


class VendorConnection(relay.Connection):
    class Meta:
        node = Vendor
