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


QUERY_CHANNELS_FILTER_BY_IS_ACTIVE = """
    query Channels($isActive: Boolean) {
        channels(isActive: $isActive) {
            slug
            isActive
        }
    }
"""


def _deactivate_channel_pln(channel_PLN):
    channel_PLN.is_active = False
    channel_PLN.save(update_fields=["is_active"])


def test_query_channels_filter_active_only(app_api_client, channel_USD, channel_PLN):
    # given
    _deactivate_channel_pln(channel_PLN)

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNELS_FILTER_BY_IS_ACTIVE, {"isActive": True}
    )
    content = get_graphql_content(response)

    # then
    channels = content["data"]["channels"]
    assert len(channels) == 1
    assert channels[0] == {"slug": channel_USD.slug, "isActive": True}


def test_query_channels_filter_active_only_as_staff_user(
    staff_api_client, channel_USD, channel_PLN
):
    # given
    _deactivate_channel_pln(channel_PLN)

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNELS_FILTER_BY_IS_ACTIVE, {"isActive": True}
    )
    content = get_graphql_content(response)

    # then
    channels = content["data"]["channels"]
    assert len(channels) == 1
    assert channels[0] == {"slug": channel_USD.slug, "isActive": True}


def test_query_channels_filter_inactive_only(app_api_client, channel_USD, channel_PLN):
    # given
    _deactivate_channel_pln(channel_PLN)

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNELS_FILTER_BY_IS_ACTIVE, {"isActive": False}
    )
    content = get_graphql_content(response)

    # then
    channels = content["data"]["channels"]
    assert len(channels) == 1
    assert channels[0] == {"slug": channel_PLN.slug, "isActive": False}


def test_query_channels_filter_inactive_only_when_all_active_returns_empty_list(
    app_api_client, channel_USD, channel_PLN
):
    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNELS_FILTER_BY_IS_ACTIVE, {"isActive": False}
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["channels"] == []


def test_query_channels_without_is_active_filter_returns_all_channels(
    app_api_client, channel_USD, channel_PLN
):
    # given
    _deactivate_channel_pln(channel_PLN)

    # when
    response = app_api_client.post_graphql(QUERY_CHANNELS_FILTER_BY_IS_ACTIVE, {})
    content = get_graphql_content(response)

    # then
    channels = content["data"]["channels"]
    assert len(channels) == 2
    assert {channel["slug"] for channel in channels} == {
        channel_USD.slug,
        channel_PLN.slug,
    }


def test_query_channels_with_null_is_active_filter_returns_all_channels(
    app_api_client, channel_USD, channel_PLN
):
    # given
    _deactivate_channel_pln(channel_PLN)

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNELS_FILTER_BY_IS_ACTIVE, {"isActive": None}
    )
    content = get_graphql_content(response)

    # then
    channels = content["data"]["channels"]
    assert len(channels) == 2
    assert {channel["slug"] for channel in channels} == {
        channel_USD.slug,
        channel_PLN.slug,
    }
