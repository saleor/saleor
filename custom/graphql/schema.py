import graphene
from .mutations import CustomCreate, CustomUpdate, CustomDelete, CustomClone
from .types import Custom
from saleor.graphql.core.utils import from_global_id_or_error
from .resolvers import resolve_custom, resolve_stocks
from saleor.graphql.core.fields import FilterInputConnectionField
from .filters import CustomFilterInput


class CustomQueries(graphene.ObjectType):
    custom = graphene.Field(
        Custom,
        description="Look up a custom by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of an custom", required=True
        ),
    )

    customs = FilterInputConnectionField(Custom, description="List of customs.",
                                         filter=CustomFilterInput())

    def resolve_custom(self,  info, **kwargs):
        custom_pk = kwargs.get("id")
        _, id = from_global_id_or_error(custom_pk, Custom)
        return resolve_custom(id)

    def resolve_customs(self,  info, **_kwargs):
        return resolve_stocks()


class CustomMutations(graphene.ObjectType):
    create_custom = CustomCreate.Field()
    update_custom = CustomUpdate.Field()
    delete_custom = CustomDelete.Field()
    custom_clone = CustomClone.Field()
