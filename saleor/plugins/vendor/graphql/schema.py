import graphene

from saleor.graphql.core.connection import create_connection_slice
from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.core.utils import from_global_id_or_error

from ..models import Vendor
from . import types
from .mutations import VendorCreate, VendorDelete, VendorUpdate


class Query(graphene.ObjectType):

    vendor = graphene.Field(
        types.Vendor,
        id=graphene.Argument(
            graphene.ID, description="ID of the vendor", required=True
        ),
        description="Look up a vendor by ID",
    )
    vendors = FilterConnectionField(types.VendorConnection)

    def resolve_vendors(root, info, **kwargs):
        # Querying a list
        qs = Vendor.objects.all()
        return create_connection_slice(qs, info, kwargs, types.VendorConnection)

    def resolve_vendor(self, info, id, **data):
        # Querying a single vebndor
        _, id = from_global_id_or_error(id, types.Vendor)
        return Vendor.objects.get(id=id)


class Mutation(graphene.ObjectType):
    vendor_create = VendorCreate.Field()
    vendor_update = VendorUpdate.Field()
    vendor_delete = VendorDelete.Field()


schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[types.Vendor],
)
