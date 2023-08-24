import graphene
from prices import Money

from .....channel import TransactionFlowStrategy
from .....shipping.models import ShippingMethodChannelListing, ShippingZone
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import AllocationStrategyEnum

QUERY_CHANNEL = """
    query getChannel($id: ID){
        channel(id: $id){
            id
            name
            slug
            currencyCode
            stockSettings{
                allocationStrategy
            }
        }
    }
"""


def test_query_channel_as_staff_user(staff_api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(QUERY_CHANNEL, variables=variables)
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert channel_data["name"] == channel_USD.name
    assert channel_data["slug"] == channel_USD.slug
    assert channel_data["currencyCode"] == channel_USD.currency_code
    allocation_strategy = channel_data["stockSettings"]["allocationStrategy"]
    assert (
        AllocationStrategyEnum[allocation_strategy].value
        == channel_USD.allocation_strategy
    )


def test_query_channel_as_app(app_api_client, channel_USD):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = app_api_client.post_graphql(QUERY_CHANNEL, variables=variables)
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert channel_data["name"] == channel_USD.name
    assert channel_data["slug"] == channel_USD.slug
    assert channel_data["currencyCode"] == channel_USD.currency_code
    allocation_strategy = channel_data["stockSettings"]["allocationStrategy"]
    assert (
        AllocationStrategyEnum[allocation_strategy].value
        == channel_USD.allocation_strategy
    )


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


QUERY_CHANNEL_ORDER_SETTINGS = """
    query getChannel($id: ID){
        channel(id: $id){
            id
            name
            slug
            currencyCode
            stockSettings{
                allocationStrategy
            }
            orderSettings {
                automaticallyConfirmAllNewOrders
                automaticallyFulfillNonShippableGiftCard
                expireOrdersAfter
                markAsPaidStrategy
                defaultTransactionFlowStrategy
                deleteExpiredOrdersAfter
                allowUnpaidOrders
            }
        }
    }
"""


def test_query_channel_order_settings_as_staff_user(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_ORDER_SETTINGS,
        variables=variables,
        permissions=[permission_manage_channels],
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert channel_data["name"] == channel_USD.name
    assert channel_data["slug"] == channel_USD.slug
    assert channel_data["currencyCode"] == channel_USD.currency_code
    allocation_strategy = channel_data["stockSettings"]["allocationStrategy"]
    assert (
        AllocationStrategyEnum[allocation_strategy].value
        == channel_USD.allocation_strategy
    )
    assert (
        channel_data["orderSettings"]["automaticallyConfirmAllNewOrders"]
        == channel_USD.automatically_confirm_all_new_orders
    )
    assert (
        channel_data["orderSettings"]["automaticallyFulfillNonShippableGiftCard"]
        == channel_USD.automatically_fulfill_non_shippable_gift_card
    )
    assert (
        channel_data["orderSettings"]["expireOrdersAfter"]
        == channel_USD.expire_orders_after
    )
    assert (
        channel_data["orderSettings"]["defaultTransactionFlowStrategy"]
        == channel_USD.default_transaction_flow_strategy.upper()
    )
    assert (
        channel_data["orderSettings"]["deleteExpiredOrdersAfter"]
        == channel_USD.delete_expired_orders_after.days
    )
    assert (
        channel_data["orderSettings"]["allowUnpaidOrders"]
        == channel_USD.allow_unpaid_orders
    )


def test_query_channel_order_settings_as_app(
    permission_manage_channels,
    app_api_client,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNEL_ORDER_SETTINGS,
        variables=variables,
        permissions=[permission_manage_channels],
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert channel_data["name"] == channel_USD.name
    assert channel_data["slug"] == channel_USD.slug
    assert channel_data["currencyCode"] == channel_USD.currency_code
    allocation_strategy = channel_data["stockSettings"]["allocationStrategy"]
    assert (
        AllocationStrategyEnum[allocation_strategy].value
        == channel_USD.allocation_strategy
    )
    assert (
        channel_data["orderSettings"]["automaticallyConfirmAllNewOrders"]
        == channel_USD.automatically_confirm_all_new_orders
    )
    assert (
        channel_data["orderSettings"]["automaticallyFulfillNonShippableGiftCard"]
        == channel_USD.automatically_fulfill_non_shippable_gift_card
    )
    assert (
        channel_data["orderSettings"]["expireOrdersAfter"]
        == channel_USD.expire_orders_after
    )
    assert (
        channel_data["orderSettings"]["defaultTransactionFlowStrategy"]
        == channel_USD.default_transaction_flow_strategy.upper()
    )


def test_query_channel_order_settings_as_staff_user_no_permission(
    staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_ORDER_SETTINGS,
        variables=variables,
    )

    # then
    assert_no_permission(response)


def test_query_channel_order_settings_as_app_no_permission(
    app_api_client,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNEL_ORDER_SETTINGS,
        variables=variables,
    )

    # then
    assert_no_permission(response)


QUERY_CHANNEL_CHECKOUT_SETTINGS = """
    query getChannel($id: ID){
        channel(id: $id){
            id
            checkoutSettings {
                useLegacyErrorFlow
            }
        }
    }
"""


def test_query_channel_checkout_settings_as_staff_user(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_USD.use_legacy_error_flow_for_checkout = False
    channel_USD.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_CHECKOUT_SETTINGS,
        variables=variables,
        permissions=[permission_manage_channels],
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert (
        channel_data["checkoutSettings"]["useLegacyErrorFlow"]
        == channel_USD.use_legacy_error_flow_for_checkout
    )


def test_query_channel_checkout_settings_as_app(
    permission_manage_channels,
    app_api_client,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNEL_CHECKOUT_SETTINGS,
        variables=variables,
        permissions=[permission_manage_channels],
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert (
        channel_data["checkoutSettings"]["useLegacyErrorFlow"]
        == channel_USD.use_legacy_error_flow_for_checkout
    )


def test_query_channel_checkout_settings_as_staff_user_no_permission(
    staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_CHECKOUT_SETTINGS,
        variables=variables,
    )

    # then
    assert_no_permission(response)


def test_query_channel_checkout_settings_as_app_no_permission(
    app_api_client,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNEL_CHECKOUT_SETTINGS,
        variables=variables,
    )

    # then
    assert_no_permission(response)


def test_query_channel_checkout_settings_with_manage_checkouts(
    permission_manage_checkouts, staff_api_client, channel_USD
):
    # given
    channel_USD.use_legacy_error_flow_for_checkout = False
    channel_USD.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_CHECKOUT_SETTINGS,
        variables=variables,
        permissions=[permission_manage_checkouts],
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert (
        channel_data["checkoutSettings"]["useLegacyErrorFlow"]
        == channel_USD.use_legacy_error_flow_for_checkout
    )


QUERY_CHANNEL_PAYMENT_SETTINGS = """
    query getChannel($id: ID){
        channel(id: $id){
            id
            paymentSettings {
                defaultTransactionFlowStrategy
            }
        }
    }
"""


def test_query_channel_payment_settings_as_staff_user(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_USD.default_transaction_flow_strategy = (
        TransactionFlowStrategy.AUTHORIZATION
    )
    channel_USD.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_PAYMENT_SETTINGS,
        variables=variables,
        permissions=[permission_manage_channels],
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert (
        channel_data["paymentSettings"]["defaultTransactionFlowStrategy"]
        == channel_USD.default_transaction_flow_strategy.upper()
    )


def test_query_channel_payment_settings_as_app(
    permission_manage_channels,
    app_api_client,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNEL_PAYMENT_SETTINGS,
        variables=variables,
        permissions=[permission_manage_channels],
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert (
        channel_data["paymentSettings"]["defaultTransactionFlowStrategy"]
        == channel_USD.default_transaction_flow_strategy.upper()
    )


def test_query_channel_payment_settings_as_staff_user_no_permission(
    staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_PAYMENT_SETTINGS,
        variables=variables,
    )

    # then
    assert_no_permission(response)


def test_query_channel_payment_settings_as_app_no_permission(
    app_api_client,
    channel_USD,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHANNEL_PAYMENT_SETTINGS,
        variables=variables,
    )

    # then
    assert_no_permission(response)


def test_query_channel_payment_settings_with_handle_payments(
    permission_manage_payments, staff_api_client, channel_USD
):
    # given
    channel_USD.default_transaction_flow_strategy = (
        TransactionFlowStrategy.AUTHORIZATION
    )
    channel_USD.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHANNEL_PAYMENT_SETTINGS,
        variables=variables,
        permissions=[permission_manage_payments],
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channel"]
    assert channel_data["id"] == channel_id
    assert (
        channel_data["paymentSettings"]["defaultTransactionFlowStrategy"]
        == channel_USD.default_transaction_flow_strategy.upper()
    )
