import graphene

from ....tests.utils import get_graphql_content

PRODUCT_VARIANTS_WHERE_QUERY = """
    query($where: ProductVariantWhereInput!, $channel: String) {
      productVariants(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            id
            name
            sku
          }
        }
      }
    }
"""


def test_product_variant_filter_by_ids(api_client, product_variant_list, channel_USD):
    # given
    ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list[:2]
    ]
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": ids}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 2
    returned_slugs = {node["node"]["sku"] for node in variants}
    assert returned_slugs == {
        product_variant_list[0].sku,
        product_variant_list[1].sku,
    }


def test_product_variant_filter_by_none_as_ids(
    api_client, product_variant_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": None}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 0


def test_product_variant_filter_by_ids_empty_list(
    api_client, product_variant_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": []}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 0
