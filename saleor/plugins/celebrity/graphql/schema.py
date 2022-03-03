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
from .mutations import (
    CelebrityCreate,
    CelebrityUpdate,
    CelebrityDelete,
)
from .filters import GroupFilterInput


class Query(graphene.ObjectType):
    celebrity = graphene.Field(
        types.Celebrity,
        id=graphene.Argument(graphene.ID, description="Celebrity ID", required=True),
        description="Look up a celebrity by ID",
    )
    celebrities = FilterConnectionField(
        types.CelebrityConnection,
        filter=GroupFilterInput(description="Filtering options for group."),
    )

    def resolve_celebrity(root, info, id, **kwargs):
        _, id = from_global_id_or_error(id, types.Celebrity)
        return models.Celebrity.objects.get(id=id)

    def resolve_celebrities(root, info, **kwargs):
        qs = models.Celebrity.objects.all()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, types.CelebrityConnection)


class Mutation(graphene.ObjectType):
    celebrity_create = CelebrityCreate.Field()
    celebrity_update = CelebrityUpdate.Field()
    celebrity_delete = CelebrityDelete.Field()


schema = build_schema(
    query=Query,
    mutation=Mutation,
    types=[types.Celebrity],
)
