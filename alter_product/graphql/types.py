import graphene
from saleor.product.models import ProductVariant
from saleor.graphql.core.connection import CountableDjangoObjectType


class AlternativeProduct(CountableDjangoObjectType):
    original_id = graphene.Int(required=True)
    original_sku = graphene.String()

    class Meta:
        model = ProductVariant

