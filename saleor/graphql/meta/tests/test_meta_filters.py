from ...tests.utils import get_graphql_content

FILTER_BY_META_QUERY = """
query filterProductsByMetadata ($filter:ProductFilterInput, $channel: String){
  products(first: 100, channel: $channel, filter: $filter){
    edges {
      node {
        slug
        metadata {
          key
          value
        }
      }
    }
  }
}
"""


def key_sort(item):
    return item["key"]


METADATA = sorted(
    [
        {
            "key": "A",
            "value": "X",
        },
        {
            "key": "B",
            "value": "Y",
        },
        {"key": "C", "value": "Z"},
    ],
    key=key_sort,
)


def test_filter_by_meta(api_client, product, channel_USD):
    # given
    for item in METADATA:
        product.store_value_in_metadata({item["key"]: item["value"]})

    product.save(update_fields=["metadata"])

    variables = {
        "channel": channel_USD.slug,
        "filter": {
            "metadata": METADATA,
        },
    }

    # when
    response = api_client.post_graphql(FILTER_BY_META_QUERY, variables)
    content = get_graphql_content(response)

    # then
    product_data = content["data"]["products"]["edges"][0]["node"]
    metadata = product_data["metadata"]

    # to guarantee order
    assert METADATA == sorted(metadata, key=key_sort)
    assert product_data["slug"] == product.slug
