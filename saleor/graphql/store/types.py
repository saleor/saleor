import graphene

from ...store import models
from ..core.connection import CountableDjangoObjectType
from ..meta.types import ObjectWithMetadata


class Store(CountableDjangoObjectType):
    description = graphene.String(
        description="The store description.",
        required=True,
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

    @staticmethod
    def resolve_page_description(root: models.Store, info):
        return "name"

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

