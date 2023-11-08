import pytest

from ..channel.utils import create_channel
from ..shop.utils import update_shop_settings
from ..utils import assign_permissions
from .utils import account_register, raw_token_create


@pytest.mark.e2e
def test_should_not_be_able_to_login_with_invalid_credentials_core_1506(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_channels,
    permission_manage_settings,
):
    # Before
    permissions = [permission_manage_channels, permission_manage_settings]
    assign_permissions(e2e_staff_api_client, permissions)

    chanel_data = create_channel(e2e_staff_api_client)
    channel_slug = chanel_data["slug"]

    input_data = {
        "enableAccountConfirmationByEmail": False,
    }

    update_shop_settings(e2e_staff_api_client, input_data)

    user_email = "user1@saleor.io"
    user_password = "Test1234!"

    # Step 1 - Create account for the new customer
    user_account = account_register(
        e2e_not_logged_api_client,
        user_email,
        user_password,
        channel_slug,
    )
    user_id = user_account["user"]["id"]
    assert user_id is not None
    assert user_account["user"]["isActive"] is True

    # Step 2 - Login with invalid password
    invalid_password = "password"
    login_data = raw_token_create(
        e2e_not_logged_api_client, user_email, invalid_password
    )
    error = login_data["data"]["tokenCreate"]["errors"][0]
    assert error["field"] == "email"
    assert error["message"] == "Please, enter valid credentials"
    assert error["code"] == "INVALID_CREDENTIALS"

    # Step 3 - Login with invalid email
    invalid_email = "invalid@email.com"
    login_data = raw_token_create(
        e2e_not_logged_api_client, invalid_email, user_password
    )
    error = login_data["data"]["tokenCreate"]["errors"][0]
    assert error["field"] == "email"
    assert error["message"] == "Please, enter valid credentials"
    assert error["code"] == "INVALID_CREDENTIALS"
