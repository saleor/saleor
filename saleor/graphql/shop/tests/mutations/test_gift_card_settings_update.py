from .....core import TimePeriodType
from .....site import GiftCardSettingsExpiryType
from .....site.error_codes import GiftCardSettingsErrorCode
from ....core.enums import TimePeriodTypeEnum
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import GiftCardSettingsExpiryTypeEnum

GIFT_CARD_SETTINGS_UPDATE_MUTATION = """
    mutation giftCardSettingsUpdate($input: GiftCardSettingsUpdateInput!) {
        giftCardSettingsUpdate(input: $ input) {
            giftCardSettings {
                expiryType
                expiryPeriod {
                    type
                    amount
                }
            }
            errors {
                code
                field
            }
        }
    }
"""


def test_gift_card_settings_update_by_staff(
    staff_api_client, site_settings, permission_manage_gift_card
):
    # given
    assert (
        site_settings.gift_card_expiry_type == GiftCardSettingsExpiryType.NEVER_EXPIRE
    )
    expiry_type = GiftCardSettingsExpiryTypeEnum.EXPIRY_PERIOD.name
    expiry_period_type = TimePeriodTypeEnum.DAY.name
    expiry_period = 50
    variables = {
        "input": {
            "expiryType": expiry_type,
            "expiryPeriod": {
                "type": expiry_period_type,
                "amount": expiry_period,
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardSettingsUpdate"]

    assert not data["errors"]
    assert data["giftCardSettings"]
    assert data["giftCardSettings"]["expiryType"] == expiry_type
    assert data["giftCardSettings"]["expiryPeriod"]["type"] == expiry_period_type
    assert data["giftCardSettings"]["expiryPeriod"]["amount"] == expiry_period


def test_gift_card_settings_update_by_app(
    app_api_client, site_settings, permission_manage_gift_card
):
    # given
    assert (
        site_settings.gift_card_expiry_type == GiftCardSettingsExpiryType.NEVER_EXPIRE
    )
    expiry_type = GiftCardSettingsExpiryTypeEnum.EXPIRY_PERIOD.name
    expiry_period_type = TimePeriodTypeEnum.DAY.name
    expiry_period = 50
    variables = {
        "input": {
            "expiryType": expiry_type,
            "expiryPeriod": {
                "type": expiry_period_type,
                "amount": expiry_period,
            },
        }
    }

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardSettingsUpdate"]

    assert not data["errors"]
    assert data["giftCardSettings"]
    assert data["giftCardSettings"]["expiryType"] == expiry_type
    assert data["giftCardSettings"]["expiryPeriod"]["type"] == expiry_period_type
    assert data["giftCardSettings"]["expiryPeriod"]["amount"] == expiry_period


def test_gift_card_settings_update_by_customer(api_client, site_settings):
    # given
    assert (
        site_settings.gift_card_expiry_type == GiftCardSettingsExpiryType.NEVER_EXPIRE
    )
    expiry_type = GiftCardSettingsExpiryTypeEnum.EXPIRY_PERIOD.name
    expiry_period_type = TimePeriodTypeEnum.DAY.name
    expiry_period = 50
    variables = {
        "input": {
            "expiryType": expiry_type,
            "expiryPeriod": {
                "type": expiry_period_type,
                "amount": expiry_period,
            },
        }
    }

    # when
    response = api_client.post_graphql(GIFT_CARD_SETTINGS_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_gift_card_settings_update_with_the_same_type(
    staff_api_client, site_settings, permission_manage_gift_card
):
    # given
    assert (
        site_settings.gift_card_expiry_type == GiftCardSettingsExpiryType.NEVER_EXPIRE
    )
    expiry_type = GiftCardSettingsExpiryTypeEnum.NEVER_EXPIRE.name
    variables = {
        "input": {
            "expiryType": expiry_type,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardSettingsUpdate"]

    assert not data["errors"]
    assert data["giftCardSettings"]
    assert data["giftCardSettings"]["expiryType"] == expiry_type
    assert data["giftCardSettings"]["expiryPeriod"] is None


def test_gift_card_settings_update_change_to_expiry_period_no_data_given(
    staff_api_client, site_settings, permission_manage_gift_card
):
    # given
    assert (
        site_settings.gift_card_expiry_type == GiftCardSettingsExpiryType.NEVER_EXPIRE
    )
    expiry_type = GiftCardSettingsExpiryTypeEnum.EXPIRY_PERIOD.name
    variables = {
        "input": {
            "expiryType": expiry_type,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardSettingsUpdate"]

    assert not data["giftCardSettings"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "expiryPeriod"
    assert data["errors"][0]["code"] == GiftCardSettingsErrorCode.REQUIRED.name


def test_gift_card_settings_update_change_to_never_expire(
    staff_api_client, site_settings, permission_manage_gift_card
):
    # given
    site_settings.gift_card_expiry_type = GiftCardSettingsExpiryType.EXPIRY_PERIOD
    site_settings.gift_card_expiry_period_type = TimePeriodType.MONTH
    site_settings.gift_card_expiry_period = 10
    expiry_type = GiftCardSettingsExpiryTypeEnum.NEVER_EXPIRE.name
    variables = {
        "input": {
            "expiryType": expiry_type,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardSettingsUpdate"]

    assert not data["errors"]
    assert data["giftCardSettings"]
    assert data["giftCardSettings"]["expiryType"] == expiry_type
    assert data["giftCardSettings"]["expiryPeriod"] is None
