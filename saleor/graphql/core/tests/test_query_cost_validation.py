import graphene
import pytest
from django.test import override_settings

from ...query_cost_map import COST_MAP
from ..const import DEFAULT_NESTED_LIST_LIMIT


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


QUERY_INLINE_FRAGMENT_BASED_ON_INTERFACE = """
query Page($assignedAttributeLimit: Int, $assignedMultiProductLimit: Int, $assignedMultiCategoryLimit: Int){
  page(slug:"about"){
    assignedAttributes(limit:$assignedAttributeLimit){
      ...on AssignedAttribute{
        attribute{
          id
        }
      }
      ...on AssignedMultiProductReferenceAttribute{
        value(limit:$assignedMultiProductLimit){
          id
        }
      }
      ...on AssignedMultiCategoryReferenceAttribute{
        value(limit:$assignedMultiCategoryLimit){
          id
        }
      }
    }
  }
}
"""


def test_query_cost_for_inline_fragments_on_interface(api_client):
    assigned_attributes_limit = 10
    assigned_multi_product_limit = 10
    assigned_multi_category_limit = 10000
    variables = {
        "assignedAttributeLimit": assigned_attributes_limit,
        "assignedMultiProductLimit": assigned_multi_product_limit,
        "assignedMultiCategoryLimit": assigned_multi_category_limit,
    }
    assert assigned_multi_category_limit > assigned_multi_product_limit

    # when
    response = api_client.post_graphql(
        QUERY_INLINE_FRAGMENT_BASED_ON_INTERFACE, variables
    )
    json_response = response.json()

    # then
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    single_page_cost = COST_MAP["Query"]["page"]["complexity"]
    single_assigned_attribute_attribute_cost = COST_MAP["AssignedAttribute"][
        "attribute"
    ]["complexity"]

    expected_cost = (
        single_page_cost
        + single_page_cost * assigned_attributes_limit
        # Cost of AssignedAttribute interface, as
        # all responses for child types will include
        # the fields requested in AssignedInterface
        # fragment
        + (
            single_page_cost
            * assigned_attributes_limit
            * single_assigned_attribute_attribute_cost
        )
        # max from requested inline fragment is used when requesting
        # multiple fragments based on the same interface
        + assigned_attributes_limit * assigned_multi_category_limit
    )
    assert query_cost == expected_cost


QUERY_SPREAD_FRAGMENTS_BASED_ON_INTERFACE = """
query Page(
  $assignedAttributeLimit: Int
  $assignedMultiProductLimit: Int
  $assignedMultiCategoryLimit: Int
) {
  page(slug: "about") {
    assignedAttributes(limit: $assignedAttributeLimit) {
      ...AssignedInterface
      ...MultiProducts
      ...MultiCategories
    }
  }
}

fragment AssignedInterface on AssignedAttribute {
  attribute {
    id
  }
}

fragment MultiProducts on AssignedMultiProductReferenceAttribute {
  value(limit: $assignedMultiProductLimit) {
    id
  }
}

fragment MultiCategories on AssignedMultiCategoryReferenceAttribute {
  value(limit: $assignedMultiCategoryLimit) {
    id
  }
}
"""


def test_query_cost_for_spread_fragments_on_interface(api_client):
    assigned_attributes_limit = 10
    assigned_multi_product_limit = 10
    assigned_multi_category_limit = 10000
    variables = {
        "assignedAttributeLimit": assigned_attributes_limit,
        "assignedMultiProductLimit": assigned_multi_product_limit,
        "assignedMultiCategoryLimit": assigned_multi_category_limit,
    }
    assert assigned_multi_category_limit > assigned_multi_product_limit

    # when
    response = api_client.post_graphql(
        QUERY_SPREAD_FRAGMENTS_BASED_ON_INTERFACE, variables
    )
    json_response = response.json()

    # then
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    single_page_cost = COST_MAP["Query"]["page"]["complexity"]
    single_assigned_attribute_attribute_cost = COST_MAP["AssignedAttribute"][
        "attribute"
    ]["complexity"]

    expected_cost = (
        single_page_cost
        + single_page_cost * assigned_attributes_limit
        # Cost of AssignedAttribute interface, as
        # all responses for child types will include
        # the fields requested in AssignedInterface
        # fragment
        + (
            single_page_cost
            * assigned_attributes_limit
            * single_assigned_attribute_attribute_cost
        )
        # max from requested spread fragment is used when requesting
        # multiple fragments based on the same interface
        + assigned_attributes_limit * assigned_multi_category_limit
    )
    assert query_cost == expected_cost


QUERY_SPREAD_AND_INLINE_FRAGMENTS_BASED_ON_INTERFACE = """
query Page(
  $assignedAttributeLimit: Int
  $assignedMultiProductLimit: Int
  $assignedMultiCategoryLimit: Int
) {
  page(slug: "about") {
    assignedAttributes(limit: $assignedAttributeLimit) {
      ...AssignedInterface
      ...MultiProducts
      ...MultiCategories
      ...on AssignedMultiCategoryReferenceAttribute{
        val: value(limit:$assignedMultiCategoryLimit){
          id
        }
      }
    }
  }
}

fragment AssignedInterface on AssignedAttribute {
  attribute {
    id
  }
}

fragment MultiProducts on AssignedMultiProductReferenceAttribute {
  value(limit: $assignedMultiProductLimit) {
    id
  }
}

fragment MultiCategories on AssignedMultiCategoryReferenceAttribute {
  value(limit: $assignedMultiCategoryLimit) {
    id
  }
}
"""


def test_query_cost_for_spread_and_inline_fragments_on_interface(api_client):
    assigned_attributes_limit = 10
    assigned_multi_product_limit = 10
    assigned_multi_category_limit = 10000
    variables = {
        "assignedAttributeLimit": assigned_attributes_limit,
        "assignedMultiProductLimit": assigned_multi_product_limit,
        "assignedMultiCategoryLimit": assigned_multi_category_limit,
    }
    assert assigned_multi_category_limit > assigned_multi_product_limit

    # when
    response = api_client.post_graphql(
        QUERY_SPREAD_AND_INLINE_FRAGMENTS_BASED_ON_INTERFACE, variables
    )
    json_response = response.json()

    # then
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    single_page_cost = COST_MAP["Query"]["page"]["complexity"]
    single_assigned_attribute_attribute_cost = COST_MAP["AssignedAttribute"][
        "attribute"
    ]["complexity"]

    expected_cost = (
        single_page_cost
        + single_page_cost * assigned_attributes_limit
        # Cost of AssignedAttribute interface, as
        # all responses for child types will include
        # the fields requested in AssignedInterface
        # fragment
        + (
            single_page_cost
            * assigned_attributes_limit
            * single_assigned_attribute_attribute_cost
        )
        # max from requested spread/inline fragments is used when requesting
        # multiple fragments based on the same interface
        + assigned_attributes_limit * assigned_multi_category_limit
        # Multiplied by 2 as the same fragment is used with alias
        + assigned_attributes_limit * assigned_multi_category_limit
    )
    assert query_cost == expected_cost


ATTRIBUTE_QUERY_WITH_LIMIT = """
query($limit: PositiveInt) {
  attributes(first:100) {
    edges {
      node {
        id
        name
        referenceTypes(limit: $limit) {
          ... on ProductType{
            id
            slug
          }
        }
      }
    }
  }
}
"""


def test_query_with_empty_not_required_limit_argument(
    api_client,
    product_type_product_single_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_variant_single_reference_attribute,
):
    # given
    product_type_product_single_reference_attribute.reference_product_types.add(
        product_type, product_type_with_product_attributes
    )
    product_type_variant_single_reference_attribute.reference_product_types.add(
        product_type
    )

    variables = {"limit": None}

    # when
    response = api_client.post_graphql(ATTRIBUTE_QUERY_WITH_LIMIT, variables)
    json_response = response.json()

    # then
    assert "errors" not in json_response
    assert json_response["data"]["attributes"]["edges"]
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    assert (
        query_cost == 100 * 1 + 100 * DEFAULT_NESTED_LIST_LIMIT
    )  # 100 attributes + 100 product types (limit value) per attribute


def test_query_with_not_required_limit_argument_not_provided(
    api_client,
    product_type_product_single_reference_attribute,
    product_type,
    product_type_with_product_attributes,
    product_type_variant_single_reference_attribute,
):
    # given
    product_type_product_single_reference_attribute.reference_product_types.add(
        product_type, product_type_with_product_attributes
    )
    product_type_variant_single_reference_attribute.reference_product_types.add(
        product_type
    )
    variables = {}

    # when
    response = api_client.post_graphql(ATTRIBUTE_QUERY_WITH_LIMIT, variables)
    json_response = response.json()

    # then
    assert "errors" not in json_response
    assert json_response["data"]["attributes"]["edges"]
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    assert (
        query_cost == 100 * 1 + 100 * DEFAULT_NESTED_LIST_LIMIT
    )  # 100 attributes + 100 product types (limit value) per attribute
