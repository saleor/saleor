import graphene
from prices import Money

from ....shipping.models import ShippingMethodChannelListing, ShippingZone
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

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


QUERY_CHANNEL = """
    query getChannel($id: ID){
        channel(id: $id){
            id
            name
            slug
            currencyCode
        }
    }
"""


def test_query_channel_as_staff_user(staff_api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(QUERY_CHANNEL, variables)
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert channel_data["name"] == channel_USD.name
    assert channel_data["slug"] == channel_USD.slug
    assert channel_data["currencyCode"] == channel_USD.currency_code


def test_query_channel_as_app(app_api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = app_api_client.post_graphql(QUERY_CHANNEL, variables)
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert channel_data["name"] == channel_USD.name
    assert channel_data["slug"] == channel_USD.slug
    assert channel_data["currencyCode"] == channel_USD.currency_code


def test_query_channel_as_customer(user_api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = user_api_client.post_graphql(QUERY_CHANNEL, variables)

    # then
    assert_no_permission(response)


def test_query_channel_as_anonymous(api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = api_client.post_graphql(QUERY_CHANNEL, variables)

    # then
    assert_no_permission(response)


def test_query_channel_by_invalid_id(staff_api_client, channel_USD):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(QUERY_CHANNEL, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["channel"] is None


def test_query_channel_with_invalid_object_type(staff_api_client, channel_USD):
    variables = {"id": graphene.Node.to_global_id("Order", channel_USD.pk)}
    response = staff_api_client.post_graphql(QUERY_CHANNEL, variables)
    content = get_graphql_content(response)
    assert content["data"]["channel"] is None


PUBLIC_QUERY_CHANNEL = """
    query getChannel(
        $slug: String,
        $countries: [CountryCode!]
    ){
        channel(slug: $slug){
            id
            slug
            countries{
                code
                country
            }
            availableShippingMethodsPerCountry(countries: $countries){
                countryCode
                shippingMethods {
                    id
                    name
                    price {
                        amount
                    }
                    name
                    maximumDeliveryDays
                    minimumDeliveryDays
                    minimumOrderPrice {
                        amount
                    }
                    maximumOrderPrice {
                        amount
                    }
                }
            }
        }
    }
"""


def test_query_channel_return_public_data_as_anonymous(api_client, channel_USD):
    # given
    variables = {"slug": channel_USD.slug}

    # when
    response = api_client.post_graphql(PUBLIC_QUERY_CHANNEL, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["channel"]


def test_query_channel_missing_id_and_slug_in_query(api_client, channel_USD):
    # given
    query = """{
    channel{
            id
        }
    }
    """

    # when
    response = api_client.post_graphql(query)

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["data"]["channel"] is None


def test_query_channel_returns_countries_attached_to_shipping_zone(
    api_client, channel_USD, channel_PLN, shipping_zone
):
    # given
    variables = {"slug": channel_PLN.slug}
    shipping_zone = ShippingZone.objects.create(
        name="Europe", countries=["PL", "DE", "FR"]
    )
    shipping_zone.channels.add(channel_PLN)

    # when
    response = api_client.post_graphql(PUBLIC_QUERY_CHANNEL, variables)

    # then
    content = get_graphql_content(response)
    channel_data = content["data"]["channel"]
    assert set([country["code"] for country in channel_data["countries"]]) == set(
        ["PL", "DE", "FR"]
    )
    assert set([country["country"] for country in channel_data["countries"]]) == set(
        ["Poland", "Germany", "France"]
    )


def test_query_channel_returns_supported_shipping_methods(
    api_client, channel_USD, channel_PLN, shipping_zone, shipping_method
):
    # given
    variables = {"slug": channel_PLN.slug}
    shipping_zone = ShippingZone.objects.create(
        name="Europe", countries=["PL", "DE", "FR"]
    )
    shipping_zone.channels.add(channel_PLN)
    shipping_method.shipping_zone = shipping_zone
    shipping_method.save()

    ShippingMethodChannelListing.objects.create(
        shipping_method=shipping_method,
        channel=channel_PLN,
        minimum_order_price=Money(0, "USD"),
        price=Money(10, "USD"),
    )

    # when
    response = api_client.post_graphql(PUBLIC_QUERY_CHANNEL, variables)

    # then
    content = get_graphql_content(response)
    channel_data = content["data"]["channel"]

    assert len(channel_data["availableShippingMethodsPerCountry"]) == 3
    sm_per_country = channel_data["availableShippingMethodsPerCountry"]
    response_country_codes = [item["countryCode"] for item in sm_per_country]
    assert {"PL", "DE", "FR"} == set(response_country_codes)
    expected_shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.id
    )

    # each country uses the same shipping method
    assert expected_shipping_method_id == sm_per_country[0]["shippingMethods"][0]["id"]
    assert expected_shipping_method_id == sm_per_country[1]["shippingMethods"][0]["id"]
    assert expected_shipping_method_id == sm_per_country[2]["shippingMethods"][0]["id"]


def test_query_channel_returns_supported_shipping_methods_with_countries_input(
    api_client, channel_USD, channel_PLN, shipping_zone, shipping_method
):
    # given
    variables = {"slug": channel_PLN.slug, "countries": ["PL"]}
    shipping_zone = ShippingZone.objects.create(
        name="Europe", countries=["PL", "DE", "FR"]
    )
    shipping_zone.channels.add(channel_PLN)
    shipping_method.shipping_zone = shipping_zone
    shipping_method.save()

    ShippingMethodChannelListing.objects.create(
        shipping_method=shipping_method,
        channel=channel_PLN,
        minimum_order_price=Money(0, "USD"),
        price=Money(10, "USD"),
    )

    # when
    response = api_client.post_graphql(PUBLIC_QUERY_CHANNEL, variables)

    # then
    content = get_graphql_content(response)
    channel_data = content["data"]["channel"]
    sm_per_country = channel_data["availableShippingMethodsPerCountry"]

    expected_shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.id
    )
    assert len(sm_per_country) == 1
    assert sm_per_country[0]["countryCode"] == "PL"
    assert len(sm_per_country[0]["shippingMethods"]) == 1
    assert sm_per_country[0]["shippingMethods"][0]["id"] == expected_shipping_method_id
