import graphene

from graphene import relay
from graphene_django.debug import DjangoDebug

from ..product.models import Category, Product, ProductAttribute
from .product_schema import CategoryType, ProductAttributeType, ProductType
from .utils import get_object_or_none


class Viewer(graphene.ObjectType):
    category = graphene.Field(
        CategoryType, pk=graphene.Argument(graphene.Int, required=True))
    product = graphene.Field(
        ProductType, pk=graphene.Argument(graphene.Int, required=True))
    attributes = graphene.List(ProductAttributeType)
    categories = relay.ConnectionField(CategoryType)
    products = relay.ConnectionField(ProductType)

    def categories_queryset(self):
        return Category.objects.prefetch_related(
            'products__images', 'products__variants',
            'products__variants__stock')

    def products_queryset(self):
        return Product.objects.prefetch_related(
            'images', 'categories', 'variants', 'variants__stock')

    def resolve_category(self, args, context, info):
        qs = self.categories_queryset()
        return get_object_or_none(qs, pk=args.get('pk'))

    def resolve_product(self, args, context, info):
        qs = self.products_queryset()
        return get_object_or_none(qs, pk=args.get('pk'))

    def resolve_attributes(self, args, context, info):
        return ProductAttribute.objects.prefetch_related('values').all()

    def resolve_categories(self, args, context, info):
        qs = self.categories_queryset()
        return qs.all()

    def resolve_products(self, args, context, info):
        qs = self.products_queryset()
        return qs.all()


class Query(graphene.ObjectType):
    viewer = graphene.Field(Viewer)
    node = relay.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_viewer(self, args, context, info):
        return Viewer()


schema = graphene.Schema(Query)
