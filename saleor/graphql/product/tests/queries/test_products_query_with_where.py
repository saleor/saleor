import graphene
import pytest

from ....tests.utils import get_graphql_content

PRODUCTS_WHERE_QUERY = """
    query($where: ProductWhereInput!, $channel: String) {
      products(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            id
            name
            slug
          }
        }
      }
    }
"""


def test_prod_filter_by_ids(api_client, product_list, channel_USD):
    # given
    ids = [
        graphene.Node.to_global_id("Product", product.pk)
        for product in product_list[:2]
    ]
    variables = {"channel": channel_USD.slug, "where": {"ids": ids}}

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 2
    returned_slugs = {node["node"]["slug"] for node in products}
    assert returned_slugs == {
        product_list[0].slug,
        product_list[1].slug,
    }


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": "Test product 1"}, [0]),
        ({"eq": "Non-existing"}, []),
        ({"oneOf": ["Test product 1", "Test product 2"]}, [0, 1]),
        ({"oneOf": ["Test product 1", "Non-existing"]}, [0]),
        ({"oneOf": ["Non-existing 1", "Non-existing 2"]}, []),
    ],
)
def test_attributes_filter_by_name(
    where, indexes, api_client, product_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "where": {"name": where}}

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}
