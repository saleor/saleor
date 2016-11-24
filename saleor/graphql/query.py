import graphene

from django.conf import settings
from graphene import relay
from graphene_django.debug import DjangoDebug

from ..product.models import Category, Product


class ProductQuery(graphene.AbstractType):
    category = relay.Node.Field(CategoryType)
    categories = relay.ConnectionField(CategoryType)
    product = relay.Node.Field(ProductType)
    products = relay.ConnectionField(ProductType)
    variant = relay.Node.Field(ProductVariantType)

    @graphene.resolve_only_args
    def resolve_categories(self):
        return Category.objects.all()

    @graphene.resolve_only_args
    def resolve_products(self):
        return Product.objects.prefetch_related(
            'categories', 'images', 'variants').all()


class Query(ProductQuery, graphene.ObjectType):
    pass


class DebugQuery(ProductQuery, graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='__debug')


if settings.DEBUG:
    schema = graphene.Schema(query=DebugQuery)
else:
    schema = graphene.Schema(Query)
