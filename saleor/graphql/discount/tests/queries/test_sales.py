from ....tests.utils import get_graphql_content


def test_sale_query(
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
    permission_manage_products,
):
    query = """
        query sales {
            sales(first: 1) {
                edges {
                    node {
                        type
                        products(first: 1) {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                        collections(first: 1) {
                            edges {
                                node {
                                    slug
                                }
                            }
                        }
                        name
                        discountValue
                        channelListings {
                            discountValue
                        }
                        startDate
                    }
                }
            }
        }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts, permission_manage_products]
    )
    channel_listing_usd = sale.channel_listings.get(channel=channel_USD)
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"][0]["node"]
    assert data["products"]["edges"][0]["node"]["name"] == sale.products.first().name

    assert data["type"] == sale.type.upper()
    assert data["name"] == sale.name
    assert (
        data["channelListings"][0]["discountValue"]
        == channel_listing_usd.discount_value
    )
    assert data["startDate"] == sale.start_date.isoformat()


def test_sale_query_with_channel_slug(
    staff_api_client, sale, permission_manage_discounts, channel_USD
):
    query = """
        query sales($channel: String) {
            sales(first: 1, channel: $channel) {
                edges {
                    node {
                        type
                        products(first: 1) {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                        discountValue
                        name
                        channelListings {
                            discountValue
                        }
                        startDate
                    }
                }
            }
        }
    """
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    channel_listing = sale.channel_listings.get()
    content = get_graphql_content(response)

    data = content["data"]["sales"]["edges"][0]["node"]

    assert data["type"] == sale.type.upper()
    assert data["name"] == sale.name
    assert data["products"]["edges"][0]["node"]["name"] == sale.products.first().name
    assert data["discountValue"] == channel_listing.discount_value
    assert data["channelListings"][0]["discountValue"] == channel_listing.discount_value
    assert data["startDate"] == sale.start_date.isoformat()


def test_sales_query(
    staff_api_client,
    sale_with_many_channels,
    sale,
    permission_manage_discounts,
    channel_USD,
    permission_manage_products,
):
    query = """
        query sales {
            sales(first: 2) {
                edges {
                    node {
                        name
                    }
                }
            }
        }
        """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts, permission_manage_products]
    )
    content = get_graphql_content(response)

    assert len(content["data"]["sales"]["edges"]) == 2


def test_sales_query_with_channel_slug(
    staff_api_client,
    sale_with_many_channels,
    sale,
    permission_manage_discounts,
    channel_PLN,
    permission_manage_products,
):
    query = """
        query sales($channel: String) {
            sales(first: 2, channel: $channel) {
                edges {
                    node {
                        name
                    }
                }
            }
        }
        """
    variables = {"channel": channel_PLN.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_discounts, permission_manage_products],
    )
    content = get_graphql_content(response)

    assert len(content["data"]["sales"]["edges"]) == 1
