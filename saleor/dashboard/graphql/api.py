import graphene
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField

from ...graphql.core.filters import DistinctFilterSet
from ...graphql.product.types import Category, resolve_categories
from ...graphql.utils import get_node
from .product.mutations import (
    CategoryCreateMutation, CategoryUpdateMutation, CategoryDelete)


class Query(graphene.ObjectType):
    categories = DjangoFilterConnectionField(
        Category, filterset_class=DistinctFilterSet,
        level=graphene.Argument(graphene.Int))
    category = graphene.Field(Category, id=graphene.Argument(graphene.ID))
    node = graphene.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_category(self, info, id):
        return get_node(info, id, only_type=Category)

    def resolve_categories(self, info, level=None, **kwargs):
        return resolve_categories(info, level)


class Mutations(graphene.ObjectType):
    category_create = CategoryCreateMutation.Field()
    category_delete = CategoryDelete.Field()
    category_update = CategoryUpdateMutation.Field()


schema = graphene.Schema(Query, Mutations)
