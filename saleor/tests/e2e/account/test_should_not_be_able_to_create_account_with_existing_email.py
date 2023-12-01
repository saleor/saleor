import pytest

from ..channel.utils import create_channel
from ..shop.utils import update_shop_settings
from ..utils import assign_permissions
from .utils import account_register, raw_account_register


@pytest.mark.e2e
def test_should_not_be_able_to_create_account_with_existing_email_core_1503(
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

    user_email = "user@saleor.io"
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

    # Step 2 - Create a new account with the same email address
    new_password = "Password1!"
    new_user_account = raw_account_register(
        e2e_not_logged_api_client,
        user_email,
        new_password,
        channel_slug,
    )
    error = new_user_account["data"]["accountRegister"]["errors"][0]
    assert error["field"] == "email"
    assert error["message"] == "User with this Email already exists."
    assert error["code"] == "UNIQUE"
