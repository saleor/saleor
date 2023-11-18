from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_SETTINGS_UPDATE_MUTATION = """
    mutation orderSettings($confirmOrders: Boolean, $fulfillGiftCards: Boolean) {
        orderSettingsUpdate(
            input: {
                automaticallyConfirmAllNewOrders: $confirmOrders
                automaticallyFulfillNonShippableGiftCard: $fulfillGiftCards
            }
        ) {
            orderSettings {
                automaticallyConfirmAllNewOrders
                automaticallyFulfillNonShippableGiftCard
                markAsPaidStrategy
            }
        }
    }
"""


def test_order_settings_update_by_staff(
    staff_api_client, permission_group_manage_orders, channel_USD, channel_PLN
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        ORDER_SETTINGS_UPDATE_MUTATION,
        {"confirmOrders": False, "fulfillGiftCards": False},
    )
    content = get_graphql_content(response)

    # then
    response_settings = content["data"]["orderSettingsUpdate"]["orderSettings"]
    assert response_settings["automaticallyConfirmAllNewOrders"] is False
    assert response_settings["automaticallyFulfillNonShippableGiftCard"] is False
    channel_PLN.refresh_from_db()
    channel_USD.refresh_from_db()
    assert channel_PLN.automatically_confirm_all_new_orders is False
    assert channel_PLN.automatically_fulfill_non_shippable_gift_card is False
    assert channel_USD.automatically_confirm_all_new_orders is False
    assert channel_USD.automatically_fulfill_non_shippable_gift_card is False


def test_order_settings_update_by_staff_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_USD,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    channel_USD.is_active = False
    channel_USD.save(update_fields=["is_active"])

    # when
    response = staff_api_client.post_graphql(
        ORDER_SETTINGS_UPDATE_MUTATION,
        {"confirmOrders": False, "fulfillGiftCards": False},
    )

    # then
    assert_no_permission(response)


def test_order_settings_update_by_staff_nothing_changed(
    staff_api_client, permission_group_manage_orders, channel_USD, channel_PLN
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    QUERY = """
        mutation {
            orderSettingsUpdate(
                input: {}
            ) {
                orderSettings {
                    automaticallyConfirmAllNewOrders
                    automaticallyFulfillNonShippableGiftCard
                }
            }
        }
    """

    # when
    response = staff_api_client.post_graphql(
        QUERY,
        {},
    )
    content = get_graphql_content(response)

    # then
    response_settings = content["data"]["orderSettingsUpdate"]["orderSettings"]
    assert response_settings["automaticallyConfirmAllNewOrders"] is True
    assert response_settings["automaticallyFulfillNonShippableGiftCard"] is True
    channel_PLN.refresh_from_db()
    channel_USD.refresh_from_db()
    assert channel_PLN.automatically_confirm_all_new_orders is True
    assert channel_PLN.automatically_fulfill_non_shippable_gift_card is True
    assert channel_USD.automatically_confirm_all_new_orders is True
    assert channel_USD.automatically_fulfill_non_shippable_gift_card is True


def test_order_settings_update_by_app(
    app_api_client, permission_manage_orders, channel_USD, channel_PLN
):
    # given
    app_api_client.app.permissions.set([permission_manage_orders])

    # when
    response = app_api_client.post_graphql(
        ORDER_SETTINGS_UPDATE_MUTATION,
        {"confirmOrders": False, "fulfillGiftCards": False},
    )
    content = get_graphql_content(response)

    # then
    response_settings = content["data"]["orderSettingsUpdate"]["orderSettings"]
    assert response_settings["automaticallyConfirmAllNewOrders"] is False
    assert response_settings["automaticallyFulfillNonShippableGiftCard"] is False
    channel_PLN.refresh_from_db()
    channel_USD.refresh_from_db()
    assert channel_PLN.automatically_confirm_all_new_orders is False
    assert channel_PLN.automatically_fulfill_non_shippable_gift_card is False
    assert channel_USD.automatically_confirm_all_new_orders is False
    assert channel_USD.automatically_fulfill_non_shippable_gift_card is False


def test_order_settings_update_by_user_without_permissions(
    user_api_client, channel_USD, channel_PLN
):
    # given

    # when
    response = user_api_client.post_graphql(
        ORDER_SETTINGS_UPDATE_MUTATION,
        {"confirmOrders": False, "fulfillGiftCards": False},
    )

    # then
    assert_no_permission(response)
    channel_PLN.refresh_from_db()
    channel_USD.refresh_from_db()
    assert channel_PLN.automatically_confirm_all_new_orders is True
    assert channel_PLN.automatically_fulfill_non_shippable_gift_card is True
    assert channel_USD.automatically_confirm_all_new_orders is True
    assert channel_USD.automatically_fulfill_non_shippable_gift_card is True
