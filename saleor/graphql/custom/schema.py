import graphene

from .mutations import CustomCreate, CustomUpdate, CustomDelete
from .types import (
    Custom
)
from ..core.fields import FilterInputConnectionField
from ...custom import models


class CustomQueries(graphene.ObjectType):
    custom = graphene.Field(
        Custom,
        id=graphene.ID(required=True, description="ID of custom"),
        description="List of the shop's custom.",
    )
    customs = FilterInputConnectionField(
        Custom, description="List custom"
    )

    def resolve_custom(self, info, **kwargs):
        custom_id = kwargs.get("id")
        print("custom_id: ", custom_id)

        custom = graphene.Node.get_node_from_global_id(info, custom_id, Custom)
        print("custom: ", custom)

        return custom

    def resolve_customs(self, info, **_kwargs):
        return models.Custom.objects.all()


class CustomMutations(graphene.ObjectType):
    custom_create = CustomCreate.Field()
    custom_update = CustomUpdate.Field()
    custom_delete = CustomDelete.Field()
