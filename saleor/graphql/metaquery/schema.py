import graphene

from saleor.graphql.account.types import User

from saleor.graphql.product.types import ProductType, Product
from ..core.fields import FilterInputConnectionField
from ..core.validators import validate_one_of_args_is_in_query

from .resolvers import (
    resolve_product_type_by_metadata,
    resolve_user_by_metadata, resolve_product_by_metadata)

from .filters import (
    ProductTypeMetadataFilterInput,
    ProductMetadataFilterInput)

class MetadataQueries(graphene.ObjectType):
    product_type_with_metadata = graphene.Field(
        ProductType,
        privateMetadataKey=graphene.String(),
        privateMetadataValue=graphene.String(),
        metadataKey=graphene.String(),
        metadataValue=graphene.String()
    )

    product_types_with_metadata = FilterInputConnectionField(
        ProductType,
        filter=ProductTypeMetadataFilterInput(
            description="Filtering options for product types with metadata."
        ),
        description="List of the shop's product types.",
    )

    user_with_metadata = graphene.Field(
        User,
        privateMetadataKey=graphene.String(),
        privateMetadataValue=graphene.String(),
        metadataKey=graphene.String(),
        metadataValue=graphene.String()
    )

    product_with_metadata = graphene.Field(
        Product,
        privateMetadataKey=graphene.String(),
        privateMetadataValue=graphene.String(),
        metadataKey=graphene.String(),
        metadataValue=graphene.String()
    )

    products_with_metadata = FilterInputConnectionField(
        Product,
        filter=ProductMetadataFilterInput(
            description="Filtering options for products with metadata."
        ),
        description="List of the shop's products.",
    )



    def resolve_product_type_with_metadata(self, info, privateMetadataKey=None, metadataKey=None,
                                           privateMetadataValue=None, metadataValue=None):
        validate_one_of_args_is_in_query("privateMetadataKey", privateMetadataKey, "metadataKey", metadataKey)

        return resolve_product_type_by_metadata(privateMetadataKey, metadataKey,
                                                privateMetadataValue, metadataValue)


    def resolve_user_with_metadata(self, info, privateMetadataKey=None, metadataKey=None,
                                           privateMetadataValue=None, metadataValue=None):
        validate_one_of_args_is_in_query("privateMetadataKey", privateMetadataKey, "metadataKey", metadataKey)

        return resolve_user_by_metadata(privateMetadataKey, metadataKey,
                                                privateMetadataValue, metadataValue)


    def resolve_product_with_metadata(self, info, privateMetadataKey=None, metadataKey=None,
                                           privateMetadataValue=None, metadataValue=None):
        validate_one_of_args_is_in_query("privateMetadataKey", privateMetadataKey, "metadataKey", metadataKey)

        return resolve_product_by_metadata(privateMetadataKey, metadataKey,
                                                privateMetadataValue, metadataValue)


