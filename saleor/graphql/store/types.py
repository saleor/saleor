import graphene

from ...store import models
from ..core.connection import CountableDjangoObjectType
from ..meta.types import ObjectWithMetadata
from ..core.types import Image


class Store(CountableDjangoObjectType):
    name = graphene.String(
        description="The store name.",
        required=True,
    )
    description = graphene.String(
        description="The store description.",
        required=True,
    )
    phone = graphene.String(
        description="The store phone.",
        required=True,
    )
    acreage = graphene.Float(
        description="The store acreage.",
        required=True,
    )
    latlong = graphene.String(
        description="The store latlong.",
        required=True,
    )
    url = graphene.String(
        description="The store's URL.",
    )
    background_image = graphene.Field(
        Image, size=graphene.Int(description="Size of the image.")
    )

    class Meta:
        description = (
            "A static page that can be manually added by a shop operator through the "
            "dashboard."
        )
        only_fields = [
            "name",
            "description"
        ]
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Store

class StoreType(CountableDjangoObjectType):
    name = graphene.String(
        description="The store name.",
        required=True,
    )
    description = graphene.String(
        description="The store description.",
        required=True,
    )

    class Meta:
        description = (
            "Represents a type of page. It defines what attributes are available to "
            "pages of this type."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.StoreType
        only_fields = ["id", "name"]

