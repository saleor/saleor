import graphene
import pytest
from django.test import override_settings


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=1)
def test_query_exceeding_cost_limit_fails_validation(
    api_client,
    variant_with_many_stocks,
    channel_USD,
):
    query_fields = "\n".join(
        [
            f"p{i}:  productVariant(id: $id, channel: $channel) {{ id }}"
            for i in range(20)
        ]
    )
    query = f"""
        query variantAvailability($id: ID!, $channel: String) {{
            {query_fields}
        }}
    """

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }

    response = api_client.post_graphql(query, variables)
    json_response = response.json()
    assert "data" not in json_response
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    assert query_cost > 1
    assert len(json_response["errors"]) == 1
    assert json_response["errors"][0]["message"] == (
        f"The query exceeds the maximum cost of 1. Actual cost is {query_cost}"
    )


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=100000)
def test_query_below_cost_limit_passes_validation(
    api_client,
    variant_with_many_stocks,
    channel_USD,
):
    query_fields = "\n".join(
        [
            f"p{i}:  productVariant(id: $id, channel: $channel) {{ id }}"
            for i in range(20)
        ]
    )
    query = f"""
        query variantQueryCost($id: ID!, $channel: String) {{
            {query_fields}
        }}
    """

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }

    response = api_client.post_graphql(query, variables)
    json_response = response.json()
    assert "errors" not in json_response
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    assert query_cost == 20
    assert len(json_response["data"]) == 20


VARIANTS_QUERY = """
    query variantsQueryCost($ids: [ID!], $channel: String, $first: Int) {
        productVariants(ids: $ids, channel: $channel, first: $first) {
            edges {
                node {
                    id
                }
            }
        }
    }
"""


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=10)
def test_query_exceeding_cost_limit_due_to_multiplied_complexity_fails_validation(
    api_client,
    variant_with_many_stocks,
    channel_USD,
):
    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk)
        ],
        "channel": channel_USD.slug,
        "first": 100,
    }

    response = api_client.post_graphql(VARIANTS_QUERY, variables)
    json_response = response.json()
    assert "data" not in json_response
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    assert query_cost > 10
    assert len(json_response["errors"]) == 1
    assert json_response["errors"][0]["message"] == (
        f"The query exceeds the maximum cost of 10. Actual cost is {query_cost}"
    )


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=10)
def test_query_below_cost_limit_with_multiplied_complexity_passes_validation(
    api_client,
    variant_with_many_stocks,
    channel_USD,
):
    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk)
        ],
        "channel": channel_USD.slug,
        "first": 5,
    }

    response = api_client.post_graphql(VARIANTS_QUERY, variables)
    json_response = response.json()
    assert "errors" not in json_response
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    assert query_cost == 5
    assert len(json_response["data"]) == 1


PRODUCTS_QUERY = """
query productsQueryCost($channel: String, $first: Int) {
  products(channel: $channel, first: $first) {
    edges {
      node {
        id
        category{
          products(channel: $channel, first: $first) {
            edges{
              node{
                id
              }
            }
          }
        }
      }
    }
  }
}
"""

PRODUCTS_QUERY_WITH_INLINE_FRAGMENT = """
query productsQueryCost($channel: String, $first: Int) {
  products(channel: $channel, first: $first) {
    edges {
      node {
        id
        category {
          ... on Category {
            products(channel: $channel, first: $first) {
              edges {
                node {
                  id
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

PRODUCTS_QUERY_WITH_FRAGMENT = """
fragment category on Category {
  products(channel: $channel, first: $first) {
    edges {
      node {
        id
      }
    }
  }
}

query productsQueryCost($channel: String, $first: Int) {
  products(channel: $channel, first: $first) {
    edges {
      node {
        id
        category {
          ...category
        }
      }
    }
  }
}
"""


@pytest.mark.parametrize(
    "query",
    [
        PRODUCTS_QUERY,
        PRODUCTS_QUERY_WITH_INLINE_FRAGMENT,
        PRODUCTS_QUERY_WITH_FRAGMENT,
    ],
)
@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=100000)
def test_query_with_fragments_have_same_multiplied_complexity_cost(
    query, api_client, product, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "first": 10}
    product_id = graphene.Node.to_global_id("Product", product.pk)
    # when
    response = api_client.post_graphql(query, variables)
    json_response = response.json()
    # then
    assert "errors" not in json_response
    expected_data = {
        "products": {
            "edges": [
                {
                    "node": {
                        "id": product_id,
                        "category": {
                            "products": {"edges": [{"node": {"id": product_id}}]}
                        },
                    }
                }
            ]
        }
    }
    assert json_response["data"] == expected_data
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    assert query_cost == 120
