from datetime import timedelta

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....product.models import ProductChannelListing
from ....tests.utils import assert_graphql_error_with_message, get_graphql_content

GET_SORTED_PRODUCTS_QUERY = """
query Products($sortBy: ProductOrder, $channel: String) {
    products(first: 10, sortBy: $sortBy, channel: $channel) {
      edges {
        node {
          id
        }
      }
    }
}
"""


@freeze_time("2020-03-18 12:00:00")
@pytest.mark.parametrize(
    "direction, order_direction",
    (("ASC", "publication_date"), ("DESC", "-publication_date")),
)
def test_sort_products_by_publication_date(
    direction, order_direction, api_client, product_list, channel_USD
):
    product_channel_listings = []
    for iter_value, product in enumerate(product_list):
        product_channel_listing = product.channel_listings.get(channel=channel_USD)
        product_channel_listing.published_at = timezone.now() - timedelta(
            days=iter_value
        )
        product_channel_listings.append(product_channel_listing)
    ProductChannelListing.objects.bulk_update(
        product_channel_listings, ["published_at"]
    )

    variables = {
        "sortBy": {
            "direction": direction,
            "field": "PUBLICATION_DATE",
        },
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(GET_SORTED_PRODUCTS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    if direction == "ASC":
        product_list.reverse()

    assert [node["node"]["id"] for node in data] == [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]


QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING = """
    query ($sortBy: ProductOrder, $filter: ProductFilterInput, $channel: String){
        products (
            first: 10, sortBy: $sortBy, filter: $filter, channel: $channel
        ) {
            edges {
                node {
                    name
                    slug
                }
            }
        }
    }
"""


def test_products_with_sorting_and_without_channel(
    staff_api_client,
    permission_manage_products,
):
    # given
    variables = {"sortBy": {"field": "PUBLICATION_DATE", "direction": "DESC"}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, "A default channel does not exist.")
