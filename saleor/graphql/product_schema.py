import graphene

from graphene import relay
from graphene_django import DjangoObjectType

from ..product.models import Category, Product, ProductImage, ProductVariant


class PriceType(graphene.ObjectType):
    gross = graphene.Float()
    net = graphene.Float()
    currency = graphene.String()


class ProductImageType(DjangoObjectType):
    url = graphene.String(size=graphene.String())

    class Meta:
        model = ProductImage
        interfaces = (relay.Node, )

    def resolve_url(self, args, context, info):
        size = args.get('size')
        if size:
            return self.image.crop[size].url
        return self.image.url


class ProductVariantType(DjangoObjectType):
    price_override = graphene.Field(PriceType)

    class Meta:
        model = ProductVariant
        interfaces = (relay.Node, )


class ProductType(DjangoObjectType):
    pk = graphene.Int()
    url = graphene.String()
    price = graphene.Field(PriceType)
    images = relay.ConnectionField(ProductImageType)
    variants = relay.ConnectionField(ProductVariantType)

    class Meta:
        model = Product
        interfaces = (relay.Node, )

    @graphene.resolve_only_args
    def resolve_images(self):
        return self.images.all()

    @graphene.resolve_only_args
    def resolve_variants(self):
        return self.variants.all()

    @graphene.resolve_only_args
    def resolve_pk(self):
        return self.pk

    @graphene.resolve_only_args
    def resolve_url(self):
        return self.get_absolute_url()


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        interfaces = (relay.Node, )
