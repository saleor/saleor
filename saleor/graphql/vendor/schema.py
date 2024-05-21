import graphene
from ...vendor import models
from .types import Vendor


class VendorQueries(graphene.ObjectType):
    vendors = graphene.List(
        Vendor,
    )

    def resolve_vendors(_root, info):
        return models.Vendor.objects.all()
