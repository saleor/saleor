import graphene
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField

from .core.filters import DistinctFilterSet
from .product.filters import ProductFilterSet
from .product.types import (
    Category, ProductAttribute, Product, resolve_attributes, resolve_products,
    resolve_categories)
from .utils import get_node


class Query(graphene.ObjectType):
    attributes = DjangoFilterConnectionField(
        ProductAttribute,
        filterset_class=DistinctFilterSet,
        in_category=graphene.Argument(graphene.ID))
    categories = DjangoFilterConnectionField(
        Category, filterset_class=DistinctFilterSet,
        level=graphene.Argument(graphene.Int))
    category = graphene.Field(Category, id=graphene.Argument(graphene.ID))
    product = graphene.Field(Product, id=graphene.Argument(graphene.ID))
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilterSet)
    node = graphene.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_category(self, info, id):
        return get_node(info, id, only_type=Category)

    def resolve_categories(self, info, level=None):
        return resolve_categories(info, level)

    def resolve_product(self, info, id):
        return get_node(info, id, only_type=Product)

    def resolve_products(self, info, **kwargs):
        return resolve_products(info)

    def resolve_attributes(self, info, in_category=None):
        return resolve_attributes(in_category, info)


schema = graphene.Schema(Query)
