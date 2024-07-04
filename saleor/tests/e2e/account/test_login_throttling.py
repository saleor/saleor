from datetime import timedelta
from unittest.mock import patch

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from ....account.error_codes import AccountErrorCode
from ....account.throttling import (
    get_cache_key_blocked_ip,
    get_cache_key_failed_ip,
    get_cache_key_failed_ip_with_user,
    get_delay_time,
)
from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils import account_register, raw_token_create


@pytest.mark.e2e
@freeze_time("2020-03-18 12:00:00")
@patch("saleor.account.throttling.get_client_ip")
@patch("saleor.account.throttling.cache")
def test_customer_should_not_be_able_to_perform_credential_guessing_attacks_core_1519(
    mocked_cache,
    mocked_get_ip,
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
    setup_mock_for_cache,
):
    # Before
    now = timezone.now()
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
    user_email = "user1@saleor.io"
    user_password = "Test1234!"

    ip = "123.123.123.123"
    mocked_get_ip.return_value = ip

    # Step 1 - Create account for the new customer
    user_account = account_register(
        e2e_not_logged_api_client,
        user_email,
        user_password,
        channel_slug,
    )
    user_id = user_account["user"]["id"]
    assert user_id is not None
    _, user_db_id = graphene.Node.from_global_id(user_id)
    assert user_account["user"]["isActive"] is True

    # Step 2 - First attempt of logging with an invalid password
    invalid_password = "password"
    login_data = raw_token_create(
        e2e_not_logged_api_client, user_email, invalid_password
    )
    error = login_data["data"]["tokenCreate"]["errors"][0]
    assert error["code"] == AccountErrorCode.INVALID_CREDENTIALS.name

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, user_db_id)

    attempt_ip_counter = 1
    attempt_ip_user_counter = 1
    delay = get_delay_time(attempt_ip_counter, attempt_ip_user_counter)
    next_attempt = now + timedelta(seconds=delay)

    assert mocked_cache.get(block_key) == next_attempt
    assert mocked_cache.get(ip_key) == attempt_ip_counter
    assert mocked_cache.get(ip_user_key) == attempt_ip_counter

    # Step 3 - Second attempt of logging with an invalid password before it is allowed
    login_data = raw_token_create(
        e2e_not_logged_api_client, user_email, invalid_password
    )
    error = login_data["data"]["tokenCreate"]["errors"][0]
    assert error["code"] == AccountErrorCode.LOGIN_ATTEMPT_DELAYED.name

    # login attempt while logining is blocked should not result in increasing
    # logging attempt counter and next allowed attempt time
    assert mocked_cache.get(block_key) == next_attempt
    assert mocked_cache.get(ip_key) == attempt_ip_counter
    assert mocked_cache.get(ip_user_key) == attempt_ip_user_counter

    # Step 4 - Third attempt of logging with an invalid password when it is allowed
    mocked_cache.delete(block_key)
    login_data = raw_token_create(
        e2e_not_logged_api_client, user_email, invalid_password
    )
    error = login_data["data"]["tokenCreate"]["errors"][0]
    assert error["code"] == AccountErrorCode.INVALID_CREDENTIALS.name

    # login attempt when logging is allowed (not blocked), should increase login attempt
    # counter and next allowed attempt time
    attempt_ip_counter += 1
    attempt_ip_user_counter += 1
    new_delay = get_delay_time(attempt_ip_counter, attempt_ip_user_counter)
    assert new_delay != delay
    next_attempt = now + timedelta(seconds=new_delay)

    assert mocked_cache.get(block_key) == next_attempt
    assert mocked_cache.get(ip_key) == attempt_ip_counter
    assert mocked_cache.get(ip_user_key) == attempt_ip_counter

    # Step 5 - Fourth attempt of logging with non-existing email when it is allowed
    non_existing_email = "non_existing_email@example.com"
    mocked_cache.delete(block_key)
    login_data = raw_token_create(
        e2e_not_logged_api_client, non_existing_email, invalid_password
    )
    error = login_data["data"]["tokenCreate"]["errors"][0]
    assert error["code"] == AccountErrorCode.INVALID_CREDENTIALS.name

    # when trying to log in with unknown email we should increase attempt for ip only
    # and not for ip+user
    assert mocked_cache.get(ip_key) == attempt_ip_counter + 1
    assert mocked_cache.get(ip_user_key) == attempt_ip_user_counter

    # Step 6 - Fifth attempt of logging with valid credentials when it is allowed
    mocked_cache.delete(block_key)
    login_data = raw_token_create(e2e_not_logged_api_client, user_email, user_password)
    assert not login_data["data"]["tokenCreate"]["errors"]
    assert login_data["data"]["tokenCreate"]["user"]["email"] == user_email

    # cache should be cleared after successful login attempt
    assert mocked_cache.get(block_key) is None
    assert mocked_cache.get(ip_key) is None
    assert mocked_cache.get(ip_user_key) is None
