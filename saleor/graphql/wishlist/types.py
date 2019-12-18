import graphene

from ...wishlist import models
from ..core.connection import CountableDjangoObjectType


class Wishlist(CountableDjangoObjectType):
    class Meta:
        only_fields = ["id", "created_at", "items"]
        description = "Wishlist item."
        interfaces = [graphene.relay.Node]
        model = models.Wishlist
        filter_fields = ["id"]


class WishlistItem(CountableDjangoObjectType):
    class Meta:
        only_fields = ["id", "wishlist", "product", "variants"]
        description = "Wishlist item."
        interfaces = [graphene.relay.Node]
        model = models.WishlistItem
        filter_fields = ["id"]
