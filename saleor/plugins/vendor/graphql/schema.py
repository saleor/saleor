import graphene
from graphene_federation import build_schema

from saleor.graphql.core.connection import (
    create_connection_slice,
    filter_connection_queryset,
)
from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.core.utils import from_global_id_or_error

from .. import models
from . import types
from .filters import VendorFilterInput
from .mutations import (
    BillingInfoCreate,
    BillingInfoDelete,
    BillingInfoUpdate,
    VendorCreate,
    VendorDelete,
    VendorUpdate,
)


class Query(graphene.ObjectType):
    vendor = graphene.Field(
        types.Vendor,
        id=graphene.Argument(
            graphene.ID, description="Vendor ID.", required=True
        ),
        description="Look up a vendor by ID",
    )
    vendors = FilterConnectionField(
        types.VendorConnection,
        filter=VendorFilterInput(description="Filtering options for vendor."),
    )

    billing = graphene.Field(
        types.Billing,
        id=graphene.Argument(graphene.ID, description="ID of Billing", required=True),
        description="Look up billing information by ID",
    )
    billings = FilterConnectionField(types.BillingConnection)

    def resolve_vendors(root, info, **kwargs):
        qs = models.Vendor.objects.all()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, types.VendorConnection)

    def resolve_vendor(self, info, id, **data):
        _, id = from_global_id_or_error(id, types.Vendor)
        return models.Vendor.objects.get(id=id)

    def resolve_billing_infos(root, info, **kwargs):
        qs = models.BillingInfo.objects.all()
        return create_connection_slice(qs, info, kwargs, types.BillingConnection)

    def resolve_billing_info(root, info, id, **data):
        _, id = from_global_id_or_error(id, types.Billing)
        return models.BillingInfo.objects.get(id=id)


class Mutation(graphene.ObjectType):
    vendor_create = VendorCreate.Field()
    vendor_update = VendorUpdate.Field()
    vendor_delete = VendorDelete.Field()
    billing_create = BillingInfoCreate.Field()
    billing_update = BillingInfoUpdate.Field()
    billing_delete = BillingInfoDelete.Field()


schema = build_schema(
    query=Query,
    mutation=Mutation,
    types=[types.Vendor],
)
