import graphene

from saleor.graphql.core.connection import CountableDjangoObjectType

from .. import models


class Wishlist(CountableDjangoObjectType):
    products = graphene.List(graphene.ID, description="List of products IDs.")
    variants = graphene.List(graphene.ID, description="List of variants IDs.")

    class Meta:
        model = models.Wishlist
        filter_fields = [
            "id",
            "token",
        ]
        interfaces = (graphene.relay.Node,)
        exclude = ["user", "token"]

    def resolve_variants(root, info):
        return [
            graphene.Node.to_global_id("ProductVariant", id)
            for id in root.variants.values_list("id", flat=True)
        ]

    def resolve_products(root, info):
        return [
            graphene.Node.to_global_id("Product", id)
            for id in root.products.values_list("id", flat=True)
        ]
