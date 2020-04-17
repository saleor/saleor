import graphene
import pytest

from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_collection_view(api_client, homepage_collection, count_queries):
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

        fragment Price on TaxedMoney {
          gross {
            amount
            currency
          }
          net {
            amount
            currency
          }
        }

        fragment ProductPricingField on Product {
          pricing {
            onSale
            priceRangeUndiscounted {
              start {
                ...Price
              }
              stop {
                ...Price
              }
            }
            priceRange {
              start {
                ...Price
              }
              stop {
                ...Price
              }
            }
          }
        }

        query Collection($id: ID!, $pageSize: Int) {
          collection(id: $id) {
            id
            slug
            name
            seoDescription
            seoTitle
            backgroundImage {
              url
            }
          }
          products(first: $pageSize, filter: {collections: [$id]}) {
            totalCount
            edges {
              node {
                ...BasicProductFields
                ...ProductPricingField
                category {
                  id
                  name
                }
              }
            }
            pageInfo {
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }
          }
          attributes(filter: {inCollection: $id}, first: 100) {
            edges {
              node {
                id
                name
                slug
                values {
                  id
                  name
                  slug
                }
              }
            }
          }
        }
    """
    variables = {
        "pageSize": 100,
        "id": graphene.Node.to_global_id("Collection", homepage_collection.pk),
    }
    get_graphql_content(api_client.post_graphql(query, variables))
