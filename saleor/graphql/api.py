import graphene
from graphene import relay
from graphene_django import DjangoConnectionField
from graphene_django.debug import DjangoDebug

from .types.cart import CartType, resolve_cart
from .types.product import (
    resolve_category, resolve_attributes, CategoryType, ProductAttributeType)
from .types.shipping import ShippingMethodType, resolve_shipping
from .types.userprofile import UserType, resolve_user


class Query(graphene.ObjectType):
    attributes = graphene.List(
        ProductAttributeType,
        category_pk=graphene.Argument(graphene.Int, required=False))
    cart = graphene.Field(CartType)
    category = graphene.Field(
        CategoryType,
        pk=graphene.Argument(graphene.Int, required=True))
    debug = graphene.Field(DjangoDebug, name='_debug')
    node = relay.Node.Field()
    root = graphene.Field(lambda: Query)
    shipping = DjangoConnectionField(ShippingMethodType)
    user = graphene.Field(UserType)

    def resolve_attributes(self, info, **args):
        category_pk = args.get('category_pk')
        return resolve_attributes(category_pk)

    def resolve_category(self, info, **args):
        pk = args.get('pk')
        return resolve_category(pk, info)

    def resolve_attributes(self, info, **args):
        category_pk = args.get('category_pk')
        return resolve_attributes(category_pk)

    def resolve_cart(self, info):
        return resolve_cart(info)

    def resolve_root(self, info):
        # Re-expose the root query object. Workaround for the issue in Relay:
        # https://github.com/facebook/relay/issues/112
        return Query()

    def resolve_shipping(self, info):
        return resolve_shipping()

    def resolve_user(self, info):
        user = info.context.user
        return resolve_user(user)


schema = graphene.Schema(Query)
