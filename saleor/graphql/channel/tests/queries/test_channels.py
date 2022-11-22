from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_CHANNELS = """
    query {
        channels {
            name
            slug
            currencyCode
            defaultCountry {
                code
                country
            }
        }
    }
"""


def test_query_channels_as_staff_user(staff_api_client, channel_USD, channel_PLN):
    # given

    # when
    response = staff_api_client.post_graphql(QUERY_CHANNELS, {})
    content = get_graphql_content(response)

    # then
    channels = content["data"]["channels"]
    assert len(channels) == 2
    assert {
        "slug": channel_PLN.slug,
        "name": channel_PLN.name,
        "currencyCode": channel_PLN.currency_code,
        "defaultCountry": {
            "code": channel_PLN.default_country.code,
            "country": channel_PLN.default_country.name,
        },
    } in channels
    assert {
        "slug": channel_USD.slug,
        "name": channel_USD.name,
        "currencyCode": channel_USD.currency_code,
        "defaultCountry": {
            "code": channel_USD.default_country.code,
            "country": channel_USD.default_country.name,
        },
    } in channels


def test_query_channels_as_app(app_api_client, channel_USD, channel_PLN):
    # given

    # when
    response = app_api_client.post_graphql(QUERY_CHANNELS, {})
    content = get_graphql_content(response)

    # then
    channels = content["data"]["channels"]
    assert len(channels) == 2
    assert {
        "slug": channel_PLN.slug,
        "name": channel_PLN.name,
        "currencyCode": channel_PLN.currency_code,
        "defaultCountry": {
            "code": channel_PLN.default_country.code,
            "country": channel_PLN.default_country.name,
        },
    } in channels
    assert {
        "slug": channel_USD.slug,
        "name": channel_USD.name,
        "currencyCode": channel_USD.currency_code,
        "defaultCountry": {
            "code": channel_USD.default_country.code,
            "country": channel_USD.default_country.name,
        },
    } in channels


def test_query_channels_as_customer(user_api_client, channel_USD, channel_PLN):
    # given

    # when
    response = user_api_client.post_graphql(QUERY_CHANNELS, {})

    # then
    assert_no_permission(response)


def test_query_channels_as_anonymous(api_client, channel_USD, channel_PLN):
    # given

    # when
    response = api_client.post_graphql(QUERY_CHANNELS, {})

    # then
    assert_no_permission(response)


QUERY_CHANNELS_WITH_HAS_ORDERS = """
query {
    channels {
        name
        slug
        currencyCode
        hasOrders
    }
}
"""


def test_query_channels_with_has_orders_order(
    staff_api_client, permission_manage_channels, channel_USD, channel_PLN, order_list
):
    # given

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNELS_WITH_HAS_ORDERS,
        {},
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    channels = content["data"]["channels"]
    assert len(channels) == 2
    assert {
        "slug": channel_PLN.slug,
        "name": channel_PLN.name,
        "currencyCode": channel_PLN.currency_code,
        "hasOrders": False,
    } in channels
    assert {
        "slug": channel_USD.slug,
        "name": channel_USD.name,
        "currencyCode": channel_USD.currency_code,
        "hasOrders": True,
    } in channels


def test_query_channels_with_has_orders_without_permission(
    staff_api_client, channel_USD, channel_PLN
):
    # given

    # when
    response = staff_api_client.post_graphql(QUERY_CHANNELS_WITH_HAS_ORDERS, {})

    # then
    assert_no_permission(response)
