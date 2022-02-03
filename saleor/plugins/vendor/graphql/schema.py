import graphene
from graphene_federation import build_schema

from saleor.graphql.core.connection import create_connection_slice
from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.core.utils import from_global_id_or_error

from .. import models
from . import types
from .mutations import (
    BillingCreate,
    BillingDelete,
    BillingUpdate,
    VendorCreate,
    VendorDelete,
    VendorUpdate,
)


class Query(graphene.ObjectType):

    vendor = graphene.Field(
        types.Vendor,
        id=graphene.Argument(
            graphene.ID, description="ID of the vendor", required=True
        ),
        description="Look up a vendor by ID",
    )
    vendors = FilterConnectionField(types.VendorConnection)

    billing = graphene.Field(
        types.Billing,
        id=graphene.Argument(graphene.ID, description="ID of Billing", required=True),
        description="Look up a billing by ID",
    )
    billings = FilterConnectionField(types.BillingConnection)

    def resolve_vendors(root, info, **kwargs):
        # Querying a list
        qs = models.Vendor.objects.all()
        return create_connection_slice(qs, info, kwargs, types.VendorConnection)

    def resolve_vendor(self, info, id, **data):
        # Querying a single vebndor
        _, id = from_global_id_or_error(id, types.Vendor)
        return models.Vendor.objects.get(id=id)

    def resolve_billings(root, info, **kwargs):
        qs = models.Billing.objects.all()
        return create_connection_slice(qs, info, kwargs, types.BillingConnection)

    def resolve_billing(root, info, id, **data):
        _, id = from_global_id_or_error(id, types.Billing)
        return models.Billing.objects.get(id=id)


class Mutation(graphene.ObjectType):
    vendor_create = VendorCreate.Field()
    vendor_update = VendorUpdate.Field()
    vendor_delete = VendorDelete.Field()
    billing_create = BillingCreate.Field()
    billing_update = BillingUpdate.Field()
    billing_delete = BillingDelete.Field()


schema = build_schema(
    query=Query,
    mutation=Mutation,
    types=[types.Vendor],
)
