from unittest import mock

import pytest

from .....account.models import User
from .....graphql.core.utils import to_global_id_or_none
from ...shop.utils import prepare_shop
from ...utils import assign_permissions
from ..utils import account_register, token_create


@mock.patch("saleor.account.throttling.cache")
@pytest.mark.e2e
def test_should_create_account_without_email_confirmation_core_1502(
    mocked_cache,
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    setup_mock_for_cache,
):
    # Before
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)

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
            }
        ],
        shop_settings={
            "enableAccountConfirmationByEmail": False,
        },
    )

    channel_slug = shop_data[0]["slug"]
    test_email = "new-user@saleor.io"
    test_password = "password!"
    redirect_url = "https://www.example.com"

    # Step 1 - Create account for the new customer
    user_account = account_register(
        e2e_not_logged_api_client,
        test_email,
        test_password,
        channel_slug,
        redirect_url,
    )
    user = User.objects.last()
    assert user
    user_id = to_global_id_or_none(user)
    assert user_account["user"]["isActive"] is True

    # Step 2 - Authenticate as new created user
    login_data = token_create(e2e_not_logged_api_client, test_email, test_password)

    assert login_data["user"]["id"] == user_id
    assert login_data["user"]["email"] == test_email
