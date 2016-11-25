import graphene

from graphene import relay
from graphene_django.debug import DjangoDebug

from ..product.models import Category, Product
from .product_schema import CategoryType, ProductType, ProductVariantType


class Viewer(graphene.ObjectType):
    category = relay.Node.Field(CategoryType)
    categories = relay.ConnectionField(CategoryType)
    product = relay.Node.Field(ProductType)
    products = relay.ConnectionField(ProductType)
    variant = relay.Node.Field(ProductVariantType)

    def resolve_categories(self, args, context, info):
        return Category.objects.all()

    def resolve_products(self, args, context, info):
        return Product.objects.prefetch_related(
            'categories', 'images', 'variants').all()


class Query(graphene.ObjectType):
    viewer = graphene.Field(Viewer)
    node = relay.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_viewer(self, args, context, info):
        return Viewer()


schema = graphene.Schema(Query)
