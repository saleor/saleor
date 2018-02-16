import graphene
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField

from .product.types import (
    Category, ProductAttribute, Product, resolve_attributes, resolve_category,
    resolve_product)
from .product.filters import DistinctFilterSet, ProductFilterSet


class Query(graphene.ObjectType):
    attributes = DjangoFilterConnectionField(
        ProductAttribute,
        filterset_class=DistinctFilterSet,
        in_category=graphene.Argument(graphene.ID))
    categories = DjangoFilterConnectionField(
        Category, filterset_class=DistinctFilterSet)
    category = graphene.Field(Category, id=graphene.Argument(graphene.ID))
    product = graphene.Field(Product, id=graphene.Argument(graphene.ID))
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilterSet)
    node = graphene.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_category(self, info, id):
        return graphene.Node.get_node_from_global_id(
            info, id, only_type=Category)

    def resolve_product(self, info, id):
        return graphene.Node.get_node_from_global_id(
            info, id, only_type=Product)

    def resolve_attributes(self, info, in_category=None):
        return resolve_attributes(in_category, info)


schema = graphene.Schema(Query)
