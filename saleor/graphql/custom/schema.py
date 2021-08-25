import graphene

from .mutations import CustomCreate, CustomUpdate, CustomDelete
from .types import (
    Custom
)
from ..core.fields import FilterInputConnectionField
from ...custom import models
from ...plugins.custom_plugin.plugin import CustomPlugin


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
        custom = CustomPlugin.detail_custom(self, info, custom_id, Custom)
        return custom

    def resolve_customs(self, info, **_kwargs):
        return models.Custom.objects.all()


class CustomMutations(graphene.ObjectType):
    custom_create = CustomCreate.Field()
    custom_update = CustomUpdate.Field()
    custom_delete = CustomDelete.Field()
