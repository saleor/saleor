import graphene
import graphql_jwt
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField

from ..page import models as page_models
from .core.filters import DistinctFilterSet
from .page.types import Page, resolve_pages
from .page.mutations import PageCreate, PageDelete, PageUpdate
from .product.filters import ProductFilterSet
from .product.mutations import (
    CategoryCreateMutation, CategoryDelete, CategoryUpdateMutation,
    ProductCreateMutation, ProductDeleteMutation, ProductUpdateMutation)
from .product.types import (
    Category, Product, ProductAttribute, resolve_attributes,
    resolve_categories, resolve_products)
from .utils import get_node


class Query(graphene.ObjectType):
    attributes = DjangoFilterConnectionField(
        ProductAttribute, filterset_class=DistinctFilterSet,
        in_category=graphene.Argument(graphene.ID),
        description='List of the shop\'s product attributes.')
    categories = DjangoFilterConnectionField(
        Category, filterset_class=DistinctFilterSet,
        level=graphene.Argument(graphene.Int),
        description='List of the shop\'s categories.')
    category = graphene.Field(
        Category, id=graphene.Argument(graphene.ID),
        description='Lookup a category by ID.')
    page = graphene.Field(
        Page, id=graphene.Argument(graphene.ID), slug=graphene.String(),
        description='Lookup a page by ID or by slug.')
    pages = DjangoFilterConnectionField(
        Page, filterset_class=DistinctFilterSet,
        level=graphene.Argument(graphene.Int),
        description='List of the shop\'s pages.')
    product = graphene.Field(
        Product, id=graphene.Argument(graphene.ID),
        description='Lookup a product by ID.')
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilterSet,
        description='List of the shop\'s products.')
    node = graphene.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_category(self, info, id):
        return get_node(info, id, only_type=Category)

    def resolve_categories(self, info, level=None, **kwargs):
        return resolve_categories(info, level)

    def resolve_page(self, info, id=None, slug=None):
        if slug is not None:
            return page_models.Page.objects.get(slug=slug)
        return get_node(info, id, only_type=Page)

    def resolve_pages(self, info):
        return resolve_pages(user=info.context.user)

    def resolve_product(self, info, id):
        return get_node(info, id, only_type=Product)

    def resolve_products(self, info, category_id=None, **kwargs):
        return resolve_products(info, category_id)

    def resolve_attributes(self, info, in_category=None, **kwargs):
        return resolve_attributes(in_category, info)


class Mutations(graphene.ObjectType):
    token_create = graphql_jwt.ObtainJSONWebToken.Field()
    token_refresh = graphql_jwt.Refresh.Field()

    category_create = CategoryCreateMutation.Field()
    category_delete = CategoryDelete.Field()
    category_update = CategoryUpdateMutation.Field()

    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_update = PageUpdate.Field()

    product_create = ProductCreateMutation.Field()
    product_delete = ProductDeleteMutation.Field()
    product_update = ProductUpdateMutation.Field()


schema = graphene.Schema(Query, Mutations)
