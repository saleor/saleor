import pytest
from graphene import Node

from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_variant_list(product_variant_list, api_client, count_queries):
    query = """
        fragment BasicProductFields on Product {
          id
          name
          thumbnail {
            url
            alt
          }
          thumbnail2x: thumbnail(size: 510) {
            url
          }
        }

        fragment ProductVariantFields on ProductVariant {
          id
          sku
          name
          stockQuantity
          isAvailable
          price {
            currency
            amount
            localized
          }
          attributes {
            attribute {
              id
              name
            }
            values {
              id
              name
              value: name
            }
          }
        }

        query VariantList($ids: [ID!]) {
          productVariants(ids: $ids, first: 100) {
            edges {
              node {
                ...ProductVariantFields
                stockQuantity
                product {
                  ...BasicProductFields
                }
              }
            }
          }
        }
    """

    variables = {
        "ids": [
            Node.to_global_id("ProductVariant", variant.pk)
            for variant in product_variant_list
        ]
    }
    get_graphql_content(api_client.post_graphql(query, variables))
