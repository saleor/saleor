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
          pricing {
            discountLocalCurrency {
              currency
              gross {
                amount
                localized
              }
            }
            price {
              currency
              gross {
                amount
                localized
              }
            }
            priceUndiscounted {
              currency
              gross {
                amount
                localized
              }
            }
            priceLocalCurrency {
              currency
              gross {
                amount
                localized
              }
            }
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
                    pricing {
                      priceRange {
                        start{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                      }
                      priceRangeUndiscounted {
                        start{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                      }
                      priceRangeLocalCurrency {
                        start{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                            localized
                          }
                        }
                      }
                    }
                  }
                }
              }
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
            isAvailable
          }
        }
    """

    variables = {"id": Node.to_global_id("Product", product.pk)}
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_attributes(product_list, api_client, count_queries):
    query = """
        query($sortBy: ProductOrder) {
          products(first: 10, sortBy: $sortBy) {
            edges {
              node {
                id
                attributes {
                  attribute {
                    id
                  }
                }
              }
            }
          }
        }
    """

    variables = {}
    get_graphql_content(api_client.post_graphql(query, variables))
