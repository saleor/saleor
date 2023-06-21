from ....tests.utils import get_graphql_content

MULTIPLE_SHIPPING_QUERY = """
    query MultipleShippings($channel: String) {
        shippingZones(first: 100, channel: $channel) {
            edges {
                node {
                    id
                    name
                    priceRange {
                        start {
                            amount
                        }
                        stop {
                            amount
                        }
                    }
                    shippingMethods {
                        channelListings {
                            price {
                                amount
                            }
                        }
                    }
                    warehouses {
                        id
                        name
                    }
                }
            }
            totalCount
        }
    }
"""


def test_shipping_zones_query(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):
    # given
    num_of_shippings = shipping_zone._meta.model.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        MULTIPLE_SHIPPING_QUERY,
        variables,
        permissions=[permission_manage_shipping, permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["shippingZones"]["totalCount"] == num_of_shippings


def test_shipping_methods_query_with_channel(
    staff_api_client,
    shipping_zone,
    shipping_method_channel_PLN,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):
    # given
    shipping_zone.shipping_methods.add(shipping_method_channel_PLN)
    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        MULTIPLE_SHIPPING_QUERY,
        variables,
        permissions=[permission_manage_shipping, permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    assert (
        len(content["data"]["shippingZones"]["edges"][0]["node"]["shippingMethods"])
        == 1
    )


def test_shipping_methods_query(
    staff_api_client,
    shipping_zone,
    shipping_method_channel_PLN,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):
    # given
    shipping_zone.shipping_methods.add(shipping_method_channel_PLN)

    # when
    response = staff_api_client.post_graphql(
        MULTIPLE_SHIPPING_QUERY,
        permissions=[permission_manage_shipping, permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    assert (
        len(content["data"]["shippingZones"]["edges"][0]["node"]["shippingMethods"])
        == 2
    )
