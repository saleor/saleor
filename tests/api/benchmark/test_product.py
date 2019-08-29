import pytest
from graphene import Node

from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_details(product, api_client, count_queries):
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

        query ProductDetails($id: ID!) {
          product(id: $id) {
            ...BasicProductFields
            description
            category {
              id
              name
              products(first: 4) {
                edges {
                  node {
                    ...BasicProductFields
                    category {
                      id
                      name
                    }
                    price {
                      amount
                      currency
                      localized
                    }
                  }
                }
              }
            }
            price {
              amount
              currency
              localized
            }
            images {
              id
              url
            }
            variants {
              ...ProductVariantFields
            }
            seoDescription
            seoTitle
            availability {
              available
            }
          }
        }
    """

    variables = {"id": Node.to_global_id("Product", product.pk)}
    get_graphql_content(api_client.post_graphql(query, variables))
