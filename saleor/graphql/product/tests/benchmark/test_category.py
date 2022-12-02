import graphene
import pytest

from .....product.models import Category
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


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_categories_for_federation_query_count(
    api_client,
    django_assert_num_queries,
    count_queries,
):
    categories = Category.objects.bulk_create(
        [
            Category(
                name="category 1", slug="category-1", lft=0, rght=1, tree_id=0, level=0
            ),
            Category(
                name="category 2", slug="category-2", lft=2, rght=3, tree_id=0, level=0
            ),
            Category(
                name="category 3", slug="category-3", lft=4, rght=5, tree_id=0, level=0
            ),
        ]
    )

    query = """
        query GetCategoryInFederation($representations: [_Any]) {
            _entities(representations: $representations) {
                __typename
                ... on Category {
                    id
                    name
                }
            }
        }
    """

    variables = {
        "representations": [
            {
                "__typename": "Category",
                "id": graphene.Node.to_global_id("Category", categories[0].pk),
            },
        ],
    }

    with django_assert_num_queries(1):
        response = api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 1

    variables = {
        "representations": [
            {
                "__typename": "Category",
                "id": graphene.Node.to_global_id("Category", category.pk),
            }
            for category in categories
        ],
    }

    with django_assert_num_queries(1):
        response = api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 3
