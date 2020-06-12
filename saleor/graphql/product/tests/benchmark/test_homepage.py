import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_list(
    api_client, homepage_collection, category, categories_tree, count_queries,
):
    query = """
        query ProductsList {
          shop {
            description
            name
            homepageCollection {
              id
              backgroundImage {
                url
              }
              name
            }
          }
          categories(level: 0, first: 4) {
            edges {
              node {
                id
                name
                backgroundImage {
                  url
                }
              }
            }
          }
        }
    """
    get_graphql_content(api_client.post_graphql(query))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_featured_products_list(api_client, homepage_collection, count_queries):
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

        query FeaturedProducts {
          shop {
            homepageCollection {
              id
              products(first: 20) {
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
              }
            }
          }
        }
    """
    get_graphql_content(api_client.post_graphql(query))
