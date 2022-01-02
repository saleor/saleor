import graphene
from saleor.graphql.core.fields import ConnectionField, FilterConnectionField

from saleor.graphql.core.connection import create_connection_slice
from saleor.graphql.core.utils import from_global_id_or_error
from . import types
from ..models import Vendor
from . import mutations


class VendorQueries(graphene.ObjectType):

    vendor = ConnectionField(types.VendorConnection)
    vendors = FilterConnectionField(types.VendorConnection)

    def resolve_vendors(root, info, **kwargs):
        # Querying a list
        qs = Vendor.objects.all()
        return create_connection_slice(qs, info, kwargs, types.VendorConnection)

    def resolve_vendor(self, info, id, **data):
        # Querying a single vebndor
        _, id = from_global_id_or_error(id, types.Vendor)
        return Vendor.objects.get(id=id)


class VendorMutations(graphene.ObjectType):
    vendor_create = mutations.VendorCreate.Field()
    vendor_update = mutations.VendorUpdate.Field()
    vendor_delete = mutations.VendorDelete.Field()


schema = graphene.Schema(
    query=VendorQueries,
    mutation=VendorMutations,
    types=[types.Vendor],
)
