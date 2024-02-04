import pytest

from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils import account_register, token_create


@pytest.mark.e2e
def test_should_login_before_email_confirmation_core_1510(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        *shop_permissions,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [
                            {},
                        ],
                    },
                ],
                "order_settings": {},
            },
        ],
        shop_settings={
            "enableAccountConfirmationByEmail": True,
            "allowLoginWithoutConfirmation": True,
        },
    )
    channel_slug = shop_data[0]["slug"]

    test_email = "user@saleor.io"
    test_password = "Password!"
    redirect_url = "https://www.example.com"

    # Step 1 - Create account for the new customer
    user_account = account_register(
        e2e_not_logged_api_client,
        test_email,
        test_password,
        channel_slug,
        redirect_url,
    )

    user_id = user_account["user"]["id"]
    assert user_account["user"]["isActive"] is True
    assert user_account["requiresConfirmation"] is True

    # Step 2 - Login

    login_data = token_create(e2e_not_logged_api_client, test_email, test_password)

    assert login_data["user"]["id"] == user_id
    assert login_data["user"]["isActive"] is True
    assert login_data["user"]["isConfirmed"] is False
