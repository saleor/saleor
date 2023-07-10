from .....core import TimePeriodType
from .....site import GiftCardSettingsExpiryType
from ....tests.utils import assert_no_permission, get_graphql_content

GIFT_CARD_SETTINGS_QUERY = """
    query giftCardSettings {
        giftCardSettings {
            expiryType
            expiryPeriod {
                type
                amount
            }
        }
    }
"""


def test_gift_card_settings_query_as_staff(
    staff_api_client, permission_manage_gift_card, site_settings
):
    # given
    assert site_settings.gift_card_expiry_period is None

    staff_api_client.user.user_permissions.add(permission_manage_gift_card)

    # when
    response = staff_api_client.post_graphql(GIFT_CARD_SETTINGS_QUERY)

    # then
    content = get_graphql_content(response)

    assert (
        content["data"]["giftCardSettings"]["expiryType"]
        == site_settings.gift_card_expiry_type.upper()
    )
    assert content["data"]["giftCardSettings"]["expiryPeriod"] is None


def test_query_gift_card_settings_expiry_period(
    staff_api_client, permission_manage_gift_card, site_settings
):
    # given
    expiry_type = GiftCardSettingsExpiryType.EXPIRY_PERIOD
    expiry_period_type = TimePeriodType.MONTH
    expiry_period = 3
    site_settings.gift_card_expiry_type = expiry_type
    site_settings.gift_card_expiry_period_type = expiry_period_type
    site_settings.gift_card_expiry_period = expiry_period
    site_settings.save(
        update_fields=[
            "gift_card_expiry_type",
            "gift_card_expiry_period_type",
            "gift_card_expiry_period",
        ]
    )

    staff_api_client.user.user_permissions.add(permission_manage_gift_card)

    # when
    response = staff_api_client.post_graphql(GIFT_CARD_SETTINGS_QUERY)

    # then
    content = get_graphql_content(response)

    assert content["data"]["giftCardSettings"]["expiryType"] == expiry_type.upper()
    assert (
        content["data"]["giftCardSettings"]["expiryPeriod"]["type"]
        == expiry_period_type.upper()
    )
    assert (
        content["data"]["giftCardSettings"]["expiryPeriod"]["amount"] == expiry_period
    )


def test_gift_card_settings_query_as_app(
    app_api_client, permission_manage_gift_card, site_settings
):
    # given
    assert site_settings.gift_card_expiry_period is None

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_SETTINGS_QUERY, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)

    assert (
        content["data"]["giftCardSettings"]["expiryType"]
        == site_settings.gift_card_expiry_type.upper()
    )
    assert content["data"]["giftCardSettings"]["expiryPeriod"] is None


def test_gift_card_settings_query_as_user(user_api_client, site_settings):
    # when
    response = user_api_client.post_graphql(GIFT_CARD_SETTINGS_QUERY)

    # then
    assert_no_permission(response)
