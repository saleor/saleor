import graphene
import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_category_view(api_client, category_with_products, count_queries, channel_USD):
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

        query Category($id: ID!, $pageSize: Int, $channel: String) {
          products (
            first: $pageSize,
            filter: {categories: [$id]},
            channel: $channel
          ) {
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
          category(id: $id) {
            seoDescription
            seoTitle
            id
            name
            backgroundImage {
              url
            }
            children(first: 10) {
              edges {
                node {
                  id
                  name
                }
              }
            }
            ancestors(last: 5) {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
          attributes(filter: {inCategory: $id}, channel: $channel, first: 100) {
            edges {
              node {
                id
                name
                slug
                choices(first: 10) {
                  edges {
                    node {
                      id
                      name
                      slug
                    }
                  }
                }
              }
            }
          }
        }
    """
    variables = {
        "pageSize": 100,
        "id": graphene.Node.to_global_id("Category", category_with_products.pk),
        "channel": channel_USD.slug,
    }
    content = get_graphql_content(api_client.post_graphql(query, variables))
    assert content["data"]["category"] is not None


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_categories_children(api_client, categories_with_children, count_queries):
    query = """query categories {
        categories(first: 30) {
          edges {
            node {
              children(first: 30) {
                edges {
                  node {
                    id
                    name
                    children(first: 30) {
                      edges {
                        node {
                          id
                          name
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }"""

    content = get_graphql_content(api_client.post_graphql(query))
    assert content["data"]["categories"] is not None


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_category_delete(
    staff_api_client,
    category_with_products,
    permission_manage_products,
    settings,
    count_queries,
):
    query = """
        mutation($id: ID!) {
            categoryDelete(id: $id) {
                category {
                    name
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    category = category_with_products
    variables = {"id": graphene.Node.to_global_id("Category", category.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["categoryDelete"]["errors"]
    assert not errors
