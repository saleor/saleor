import graphene

from ...store import models
from ..core.connection import CountableDjangoObjectType
from ..meta.types import ObjectWithMetadata
from ..core.types import Image

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
    store_type = graphene.Field(
        StoreType,
        id=graphene.Argument(graphene.ID, description="ID of the store type."),
        description="Look up a store type by ID",
    )
    background_image = graphene.Field(
        Image, size=graphene.Int(description="Size of the image.")
    )
    user_name = graphene.String(
        description="Owner of store",
    )

    class Meta:
        description = (
            "A static page that can be manually added by a shop operator through the "
            "dashboard."
        )
        only_fields = [
            "name",
            "description",
            "store_type",
            "date_joined",
            "latlong",
            "acreage",
            "url",
            "phone"
        ]
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Store