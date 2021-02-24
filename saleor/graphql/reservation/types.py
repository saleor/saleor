import graphene

from ...reservation import models
from ..channel import ChannelContext
from ..core.connection import CountableDjangoObjectType
from ..product.types import ProductVariant


class Reservation(CountableDjangoObjectType):
    class Meta:
        only_fields = ["quantity", "expires"]
        description = "Product reservation for an authenticated user."
        model = models.Reservation
        interfaces = [graphene.relay.Node]


class RemovedReservation(graphene.ObjectType):
    variant = graphene.Field(ProductVariant)
    quantity = graphene.Int()

    class Meta:
        description = "Removed product reservation for an authenticated user."

    @staticmethod
    def resolve_variant(root: dict, *_args):
        return ChannelContext(node=root.get("variant"), channel_slug=None)
