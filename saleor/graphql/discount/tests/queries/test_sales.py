from ....tests.utils import get_graphql_content


def test_sale_query(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
    permission_manage_products,
    product,
):
    # given
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
                        endDate
                        created
                        updatedAt
                    }
                }
            }
        }
    """
    promotion = promotion_converted_from_sale
    rule = promotion.rules.first()

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts, permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"][0]["node"]
    assert data["products"]["edges"][0]["node"]["name"] == product.name

    assert data["type"] == rule.reward_value_type.upper()
    assert data["name"] == promotion.name
    assert data["channelListings"][0]["discountValue"] == rule.reward_value
    assert data["startDate"] == promotion.start_date.isoformat()


def test_sale_query_with_channel_slug(
    staff_api_client,
    promotion_converted_from_sale,
    permission_manage_discounts,
    channel_USD,
    product,
):
    # given
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
    promotion = promotion_converted_from_sale
    rule = promotion.rules.first()
    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"][0]["node"]
    assert data["type"] == rule.reward_value_type.upper()
    assert data["name"] == promotion.name
    assert data["products"]["edges"][0]["node"]["name"] == product.name
    assert data["discountValue"] == rule.reward_value
    assert data["channelListings"][0]["discountValue"] == rule.reward_value
    assert data["startDate"] == promotion.start_date.isoformat()


def test_sales_query(
    staff_api_client,
    promotion_converted_from_sale,
    promotion_converted_from_sale_with_empty_predicate,
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
    promotion_converted_from_sale_with_empty_predicate,
    promotion_converted_from_sale_with_many_channels,
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


def test_sales_query_channel_listing(
    staff_api_client,
    promotion_converted_from_sale_with_many_channels,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
):
    # given
    query = """
        query sales {
            sales(first: 10) {
                edges {
                    node {
                        channelListings {
                            id
                            channel {
                                slug
                            }
                            discountValue
                            currency
                        }
                    }
                }
            }
        }
        """

    # when
    response = staff_api_client.post_graphql(
        query,
        {},
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == 1
    channel_listings = data[0]["node"]["channelListings"]
    assert len(channel_listings) == 2
    assert {listing["channel"]["slug"] for listing in channel_listings} == {
        channel_PLN.slug,
        channel_USD.slug,
    }
