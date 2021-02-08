import graphene

from ...reservation import models
from ..channel import ChannelContext
from ..core.connection import CountableDjangoObjectType
from ..product.types import ProductVariant


class Reservation(CountableDjangoObjectType):
    class Meta:
        only_fields = ["quantity", "product_variant", "expires"]
        description = "Product reservation for an authenticated user."
        model = models.Reservation
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_product_variant(root: models.Reservation, *_args):
        return root.product_variant


class RemovedReservation(graphene.ObjectType):
    product_variant = graphene.Field(ProductVariant)
    quantity = graphene.Int()

    class Meta:
        description = "Removed product reservation for an authenticated user."

    @staticmethod
    def resolve_product_variant(root: dict, *_args):
        return ChannelContext(node=root.get("product_variant"), channel_slug=None)
