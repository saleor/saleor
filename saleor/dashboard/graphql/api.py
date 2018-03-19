import graphene
import graphql_jwt
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import staff_member_required

from ...graphql.core.filters import DistinctFilterSet
from ...graphql.page.types import Page
from ...graphql.product.types import Category, Product, resolve_categories
from ...graphql.utils import get_node
from ...product import models as product_models
from .page.mutations import PageCreate, PageDelete, PageUpdate
from .page.types import resolve_all_pages
from .product.filters import ProductFilter
from .product.mutations import (
    CategoryCreateMutation, CategoryDelete, CategoryUpdateMutation)


class Query(graphene.ObjectType):
    node = graphene.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    categories = DjangoFilterConnectionField(
        Category, filterset_class=DistinctFilterSet,
        level=graphene.Argument(graphene.Int))
    category = graphene.Field(Category, id=graphene.Argument(graphene.ID))

    page = graphene.Field(Page, id=graphene.Argument(graphene.ID))
    pages = DjangoFilterConnectionField(
        Page, filterset_class=DistinctFilterSet)

    product = graphene.Field(Product, id=graphene.Argument(graphene.ID))
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilter,
        categoryID=graphene.Argument(graphene.ID))

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

    def resolve_product(self, info, id):
        return get_node(info, id, only_type=Product)

    def resolve_products(self, info, categoryID=None, **kwargs):
        if categoryID is not None:
            category = get_node(info, categoryID, only_type=Category)
            return product_models.Product.objects.filter(
                category=category).distinct()
        return product_models.Product.objects.all().distinct()


class Mutations(graphene.ObjectType):
    category_create = CategoryCreateMutation.Field()
    category_delete = CategoryDelete.Field()
    category_update = CategoryUpdateMutation.Field()

    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_update = PageUpdate.Field()

    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(Query, Mutations)
