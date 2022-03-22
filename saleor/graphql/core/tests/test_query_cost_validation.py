import graphene
from django.test import override_settings


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=1)
def test_query_exceeding_cost_limit_fails_validation(
    api_client,
    variant_with_many_stocks,
    channel_USD,
):
    query_fields = "\n".join(
        [
            "p%s:  productVariant(id: $id, channel: $channel) { id }" % i
            for i in range(20)
        ]
    )
    query = (
        """
        query variantAvailability($id: ID!, $channel: String) {
            %s
        }
    """
        % query_fields
    )

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
            "p%s:  productVariant(id: $id, channel: $channel) { id }" % i
            for i in range(20)
        ]
    )
    query = (
        """
        query variantQueryCost($id: ID!, $channel: String) {
            %s
        }
    """
        % query_fields
    )

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
