import pytest

from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils import account_register, token_create


@pytest.mark.e2e
def test_should_create_account_without_email_confirmation_core_1502(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_taxes,
    permission_manage_settings,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_shipping,
        permission_manage_taxes,
        permission_manage_settings,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_shop(
        e2e_staff_api_client,
        enable_account_confirmation_by_email=False,
    )
    channel_slug = shop_data["channel_slug"]
    test_email = "new-user@saleor.io"
    test_password = "password!"
    redirect_url = ""

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

    # Step 2 - Authenticate as new created user

    login_data = token_create(e2e_not_logged_api_client, test_email, test_password)

    assert login_data["user"]["id"] == user_id
    assert login_data["user"]["email"] == test_email
