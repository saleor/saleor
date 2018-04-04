import graphene
import graphql_jwt
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import staff_member_required

from ...graphql.core.filters import DistinctFilterSet
from ...graphql.page.types import Page
from ...graphql.product.types import (
    Category, Product, ProductAttribute, resolve_categories)
from ...graphql.utils import get_node
from .page.mutations import PageCreate, PageDelete, PageUpdate
from .page.types import resolve_all_pages
from .product.filters import ProductFilter
from .product.mutations import (
    CategoryCreateMutation, CategoryDelete, CategoryUpdateMutation)
from .product.types import resolve_attributes, resolve_products


class Query(graphene.ObjectType):
    attributes = DjangoFilterConnectionField(
        ProductAttribute, filterset_class=DistinctFilterSet,
        description='List of the shop\'s product attributes.')
    categories = DjangoFilterConnectionField(
        Category, filterset_class=DistinctFilterSet,
        level=graphene.Argument(graphene.Int),
        description='List of shop\'s categories.')
    category = graphene.Field(
        Category, id=graphene.Argument(graphene.ID),
        description='Lookup a category by ID.')
    page = graphene.Field(
        Page, id=graphene.Argument(graphene.ID),
        description='Lookup a page by ID.')
    pages = DjangoFilterConnectionField(
        Page, filterset_class=DistinctFilterSet,
        description='List of shop\'s pages.')
    product = graphene.Field(
        Product, id=graphene.Argument(graphene.ID),
        description='Lookup a product by ID.')
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilter,
        category_id=graphene.Argument(graphene.ID),
        description='List of shop\'s products.')
    node = graphene.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    @staff_member_required
    def resolve_attributes(self, info):
        return resolve_attributes()

    @staff_member_required
    def resolve_category(self, info, id):
        return get_node(info, id, only_type=Category)

    @staff_member_required
    def resolve_categories(self, info, level=None, **kwargs):
        return resolve_categories(info, level)

    @staff_member_required
    def resolve_page(self, info, id):
        return get_node(info, id, only_type=Page)

    @staff_member_required
    def resolve_pages(self, info):
        return resolve_all_pages()

    @staff_member_required
    def resolve_product(self, info, id):
        return get_node(info, id, only_type=Product)

    @staff_member_required
    def resolve_products(self, info, category_id=None, **kwargs):
        return resolve_products(info, category_id)


class Mutations(graphene.ObjectType):
    category_create = CategoryCreateMutation.Field()
    category_delete = CategoryDelete.Field()
    category_update = CategoryUpdateMutation.Field()

    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_update = PageUpdate.Field()

    token_create = graphql_jwt.ObtainJSONWebToken.Field()
    token_refresh = graphql_jwt.Refresh.Field()


schema = graphene.Schema(Query, Mutations)
