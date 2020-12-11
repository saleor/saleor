import graphene

from ...reservation import models
from ..core.connection import CountableDjangoObjectType


class Reservation(CountableDjangoObjectType):
    class Meta:
        only_fields = ["quantity", "product_variant", "expires"]
        description = "Product reservation for an authenticated user."
        model = models.Reservation
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_product_variant(root: models.Reservation, *_args):
        return root.product_variant
