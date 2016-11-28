import datetime
import graphene

from graphene import relay
from graphene_django import DjangoObjectType

from ..product.models import Category, Product, ProductImage, ProductVariant
from .utils import DjangoPkInterface


class PriceType(graphene.ObjectType):
    gross = graphene.Float()
    net = graphene.Float()
    currency = graphene.String()


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


class ProductVariantType(DjangoObjectType):
    price_override = graphene.Field(PriceType)
    stock_quantity = graphene.Int()

    class Meta:
        model = ProductVariant
        interfaces = (relay.Node, DjangoPkInterface)

    @graphene.resolve_only_args
    def resolve_stock_quantity(self):
        return self.get_stock_quantity()


class ProductType(DjangoObjectType):
    url = graphene.String()
    price = graphene.Field(PriceType)
    image_url = graphene.String()
    images = graphene.List(ProductImageType)
    is_available = graphene.Boolean()
    variants = graphene.List(ProductVariantType)

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


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        interfaces = (relay.Node, DjangoPkInterface)
