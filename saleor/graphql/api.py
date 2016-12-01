import datetime
import graphene

from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.debug import DjangoDebug

from ..product.models import (AttributeChoiceValue, Category, Product,
                              ProductAttribute, ProductImage, ProductVariant)
from .utils import DjangoPkInterface, get_object_or_none


def resolve_products(root, args, context, info):
    pass


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        interfaces = (relay.Node, DjangoPkInterface)


class ProductType(DjangoObjectType):
    url = graphene.String()
    image_url = graphene.String()
    is_available = graphene.Boolean()
    price = graphene.Field(lambda: PriceType)
    images = graphene.List(lambda: ProductImageType)
    variants = graphene.List(lambda: ProductVariantType)

    class Meta:
        model = Product
        interfaces = (relay.Node, DjangoPkInterface)

    @graphene.resolve_only_args
    def resolve_is_available(self):
        today = datetime.date.today()
        return self.available_on is None or self.available_on >= today

    @graphene.resolve_only_args
    def resolve_image_url(self):
        return self.images.first().image.crop['400x400'].url

    @graphene.resolve_only_args
    def resolve_images(self):
        return self.images.all()

    @graphene.resolve_only_args
    def resolve_variants(self):
        return self.variants.all()

    @graphene.resolve_only_args
    def resolve_url(self):
        return self.get_absolute_url()


class ProductVariantType(DjangoObjectType):
    stock_quantity = graphene.Int()
    price_override = graphene.Field(lambda: PriceType)

    class Meta:
        model = ProductVariant
        interfaces = (relay.Node, DjangoPkInterface)

    @graphene.resolve_only_args
    def resolve_stock_quantity(self):
        return self.get_stock_quantity()


class ProductImageType(DjangoObjectType):
    url = graphene.String(size=graphene.String())

    class Meta:
        model = ProductImage
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_url(self, args, context, info):
        size = args.get('size')
        if size:
            return self.image.crop[size].url
        return self.image.url


class ProductAttributeValue(DjangoObjectType):
    class Meta:
        model = AttributeChoiceValue
        interfaces = (relay.Node, DjangoPkInterface)


class ProductAttributeType(DjangoObjectType):
    values = graphene.List(lambda: ProductAttributeValue)

    class Meta:
        model = ProductAttribute
        interfaces = (relay.Node, DjangoPkInterface)

    @graphene.resolve_only_args
    def resolve_values(self):
        return self.values.all()


class PriceType(graphene.ObjectType):
    gross = graphene.Float()
    net = graphene.Float()
    currency = graphene.String()


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
