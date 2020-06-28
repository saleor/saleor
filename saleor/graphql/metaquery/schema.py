import graphene

from saleor.graphql.product.types import ProductType
from ..core.fields import FilterInputConnectionField
from ..core.validators import validate_one_of_args_is_in_query

from .resolvers import (
    resolve_product_type_by_metadata,
)

from .filters import (
    ProductTypeMetadataFilterInput
)

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

    def resolve_product_type_with_metadata(self, info, privateMetadataKey=None, metadataKey=None,
                                           privateMetadataValue=None, metadataValue=None):
        validate_one_of_args_is_in_query("privateMetadataKey", privateMetadataKey, "metadataKey", metadataKey)

        # params = {}
        # if privateMetadataKey and privateMetadataValue:
        #     params["privateMetadataKey"] = privateMetadataKey
        #     params["privateMetadataValue"] = privateMetadataValue
        #
        # if metadataKey and metadataValue:
        #     params["metadataKey"] = metadataKey
        #     params["metadataValue"] = metadataValue

        return resolve_product_type_by_metadata(privateMetadataKey, metadataKey,
                                                privateMetadataValue, metadataValue)


