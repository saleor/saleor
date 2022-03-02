import graphene
from graphene import relay

from ....graphql.core.connection import CountableDjangoObjectType
from .. import models


class Vendor(CountableDjangoObjectType):
    users = graphene.List(graphene.ID, description="List of user IDs.")

    variants = graphene.List(graphene.ID, description="List of variant IDs.")

    class Meta:
        model = models.Vendor
        filter_fields = ["id", "name", "country"]
        interfaces = (graphene.relay.Node,)

    def resolve_users(root, info):
        return root.users.values_list("id")

    def resolve_variants(root, info):
        return root.variants.values_list("id")


class VendorConnection(relay.Connection):
    class Meta:
        node = Vendor


class Billing(CountableDjangoObjectType):
    class Meta:
        model = models.BillingInfo
        filter_fields = ["id", "iban", "bank_name"]
        interfaces = (graphene.relay.Node,)


class BillingConnection(relay.Connection):
    class Meta:
        node = Billing
