from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_SETTINGS_QUERY = """
    query orderSettings {
        orderSettings {
            automaticallyConfirmAllNewOrders
            automaticallyFulfillNonShippableGiftCard
        }
    }
"""


def test_order_settings_query_one_channel(
    staff_api_client, permission_manage_orders, channel_USD
):
    # given
    channel_USD.automatically_confirm_all_new_orders = False
    channel_USD.automatically_fulfill_non_shippable_gift_card = True
    channel_USD.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_SETTINGS_QUERY)

    # then
    content = get_graphql_content(response)

    assert content["data"]["orderSettings"]["automaticallyConfirmAllNewOrders"] is False
    assert (
        content["data"]["orderSettings"]["automaticallyFulfillNonShippableGiftCard"]
        is True
    )


def test_order_settings_query_multiple_channels(
    staff_api_client, permission_manage_orders, channel_USD, channel_PLN
):
    # given
    channel_USD.automatically_confirm_all_new_orders = False
    channel_USD.automatically_fulfill_non_shippable_gift_card = True
    channel_USD.save()

    channel_PLN.automatically_confirm_all_new_orders = True
    channel_PLN.automatically_fulfill_non_shippable_gift_card = False
    channel_PLN.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_SETTINGS_QUERY)

    # then
    content = get_graphql_content(response)

    assert content["data"]["orderSettings"]["automaticallyConfirmAllNewOrders"] is True
    assert (
        content["data"]["orderSettings"]["automaticallyFulfillNonShippableGiftCard"]
        is False
    )


def test_order_settings_query_as_user(user_api_client, channel_USD, channel_PLN):
    # when
    response = user_api_client.post_graphql(ORDER_SETTINGS_QUERY)

    # then
    assert_no_permission(response)
