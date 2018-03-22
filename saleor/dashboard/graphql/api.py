import graphene
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField

from ...graphql.core.filters import DistinctFilterSet
from ...graphql.page.types import Page
from ...graphql.product.types import Category, resolve_categories
from ...graphql.utils import get_node
from .page.mutations import PageCreate, PageDelete, PageUpdate
from .page.types import resolve_all_pages
from .product.mutations import (
    CategoryCreateMutation, CategoryDelete, CategoryUpdateMutation)


class Query(graphene.ObjectType):
    categories = DjangoFilterConnectionField(
        Category, filterset_class=DistinctFilterSet,
        level=graphene.Argument(graphene.Int))
    category = graphene.Field(Category, id=graphene.Argument(graphene.ID))
    node = graphene.Node.Field()
    page = graphene.Field(Page, id=graphene.Argument(graphene.ID))
    pages = DjangoFilterConnectionField(
        Page, filterset_class=DistinctFilterSet)

    def resolve_category(self, info, id):
        return get_node(info, id, only_type=Category)

    def resolve_categories(self, info, level=None, **kwargs):
        return resolve_categories(info, level)

    def resolve_page(self, info, id):
        return get_node(info, id, only_type=Page)

    def resolve_pages(self, info, **kwargs):
        return resolve_all_pages()


class Mutations(graphene.ObjectType):
    category_create = CategoryCreateMutation.Field()
    category_delete = CategoryDelete.Field()
    category_update = CategoryUpdateMutation.Field()

    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_update = PageUpdate.Field()


schema = graphene.Schema(Query, Mutations)
