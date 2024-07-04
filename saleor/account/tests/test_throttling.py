import logging
from datetime import timedelta
from unittest.mock import patch

import before_after
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from freezegun import freeze_time

from ..error_codes import AccountErrorCode
from ..throttling import (
    MAX_DELAY,
    MIN_DELAY,
    authenticate_with_throttling,
    get_cache_key_blocked_ip,
    get_cache_key_failed_ip,
    get_cache_key_failed_ip_with_user,
    get_delay_time,
)

CORRECT_PASSWORD = "password"
INCORRECT_PASSWORD = "incorrect-password"
EXISTING_EMAIL = "test@example.com"
NON_EXISTING_EMAIL = "non-existing@example.com"


@pytest.mark.parametrize(
    ("ip_attempts_count", "ip_user_attempts_count", "expected_delay"),
    [
        (1, 0, 1),
        (0, 1, 1),
        (21, 1, 4),
        (21, 4, 8),
        (100, 1, MAX_DELAY),
        (1, 10, MAX_DELAY),
        (0, 0, 1),
        (-1, -17, 1),
    ],
)
def test_get_delay_time(ip_attempts_count, ip_user_attempts_count, expected_delay):
    # given & when
    delay = get_delay_time(ip_attempts_count, ip_user_attempts_count)

    # then
    assert delay == expected_delay


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_successful_first_attempt(
    mocked_cache, rf, customer_user, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # when
    user = authenticate_with_throttling(request, EXISTING_EMAIL, CORRECT_PASSWORD)

    # then
    assert user

    assert mocked_cache.get(block_key) is None
    assert mocked_cache.get(ip_key) is None
    assert mocked_cache.get(ip_user_key) is None

    next_attempt = now + timedelta(seconds=MIN_DELAY)
    mocked_cache.add.assert_called_once_with(block_key, next_attempt, timeout=MIN_DELAY)
    mocked_cache.set.assert_not_called()
    mocked_cache.incr.assert_not_called()
    mock_delete_arg_set = {arg.args[0] for arg in mocked_cache.delete.call_args_list}
    assert {block_key, ip_key, ip_user_key} == mock_delete_arg_set


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_successful_subsequent_attempt(
    mocked_cache, rf, customer_user, setup_mock_for_cache
):
    """Make sure cache is cleared after successful login."""
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state after a couple of login attempts
    dummy_cache[ip_key] = {"value": 21, "ttl": 100}
    dummy_cache[ip_user_key] = {"value": 7, "ttl": 100}

    # when
    user = authenticate_with_throttling(request, EXISTING_EMAIL, CORRECT_PASSWORD)

    # then
    assert user

    assert mocked_cache.get(block_key) is None
    assert mocked_cache.get(ip_key) is None
    assert mocked_cache.get(ip_user_key) is None

    next_attempt = now + timedelta(seconds=MIN_DELAY)
    mocked_cache.add.assert_called_once_with(block_key, next_attempt, timeout=MIN_DELAY)
    mocked_cache.set.assert_not_called()
    mocked_cache.incr.assert_not_called()
    mock_delete_arg_set = {arg.args[0] for arg in mocked_cache.delete.call_args_list}
    assert {block_key, ip_key, ip_user_key} == mock_delete_arg_set


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_incorrect_password_non_existing_email_first_attempt(
    mocked_cache,
    rf,
    customer_user,
    setup_mock_for_cache,
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # when
    user = authenticate_with_throttling(request, NON_EXISTING_EMAIL, INCORRECT_PASSWORD)

    # then
    assert not user
    next_attempt = mocked_cache.get(block_key)
    ip_attempts_count = mocked_cache.get(ip_key)
    ip_user_attempts_count = mocked_cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=MIN_DELAY)
    assert ip_attempts_count == 1
    assert ip_user_attempts_count is None
    mock_incr_arg_set = {arg.args[0] for arg in mocked_cache.incr.call_args_list}
    assert ip_user_key not in mock_incr_arg_set


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_incorrect_password_non_existing_email_subsequent_attempt(
    mocked_cache,
    rf,
    customer_user,
    setup_mock_for_cache,
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state after a couple of login attempts
    ip_attempts_count = 21
    dummy_cache[ip_key] = {"value": ip_attempts_count, "ttl": 100}
    expected_delay = get_delay_time(ip_attempts_count + 1, 0)

    # when
    user = authenticate_with_throttling(request, NON_EXISTING_EMAIL, INCORRECT_PASSWORD)

    # then
    assert not user
    next_attempt = mocked_cache.get(block_key)
    updated_ip_attempts_count = mocked_cache.get(ip_key)
    ip_user_attempts_count = mocked_cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=expected_delay)
    assert updated_ip_attempts_count == ip_attempts_count + 1
    assert ip_user_attempts_count is None
    mock_incr_arg_set = {arg.args[0] for arg in mocked_cache.incr.call_args_list}
    assert ip_user_key not in mock_incr_arg_set


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_incorrect_password_existing_email_first_attempt(
    mocked_cache,
    rf,
    customer_user,
    setup_mock_for_cache,
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # when
    user = authenticate_with_throttling(request, EXISTING_EMAIL, INCORRECT_PASSWORD)

    # then
    assert not user
    next_attempt = mocked_cache.get(block_key)
    ip_attempts_count = mocked_cache.get(ip_key)
    ip_user_attempts_count = mocked_cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=MIN_DELAY)
    assert ip_attempts_count == 1
    assert ip_user_attempts_count == 1


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_incorrect_password_existing_email_subsequent_attempt(
    mocked_cache,
    rf,
    customer_user,
    setup_mock_for_cache,
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state after a couple of login attempts
    ip_attempts_count = 21
    ip_user_attempts_count = 5
    dummy_cache[ip_key] = {"value": ip_attempts_count, "ttl": 100}
    dummy_cache[ip_user_key] = {"value": ip_user_attempts_count, "ttl": 100}
    expected_delay = get_delay_time(ip_attempts_count + 1, ip_user_attempts_count + 1)

    # when
    user = authenticate_with_throttling(request, EXISTING_EMAIL, INCORRECT_PASSWORD)

    # then
    assert not user
    next_attempt = mocked_cache.get(block_key)
    updated_ip_attempts_count = mocked_cache.get(ip_key)
    updated_ip_user_attempts_count = mocked_cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=expected_delay)
    assert updated_ip_attempts_count == ip_attempts_count + 1
    assert updated_ip_user_attempts_count == ip_user_attempts_count + 1


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_unidentified_ip_address(rf, customer_user, caplog):
    # given
    request = rf.request(HTTP_X_FORWARDED_FOR="", REMOTE_ADDR="")
    caplog.set_level(logging.WARNING)

    # when & then
    with pytest.raises(ValidationError) as e:
        authenticate_with_throttling(request, EXISTING_EMAIL, CORRECT_PASSWORD)

    assert e.value.code == AccountErrorCode.UNKNOWN_IP_ADDRESS.value
    assert "Unknown request's IP address." in caplog.text


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_login_attempt_delayed(
    mocked_cache, rf, customer_user, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state when login is temporarily blocked
    ip_attempts_count = 21
    ip_user_attempts_count = 5
    dummy_cache[ip_key] = {"value": ip_attempts_count, "ttl": 100}
    dummy_cache[ip_user_key] = {"value": ip_user_attempts_count, "ttl": 100}
    delay = get_delay_time(ip_attempts_count, ip_user_attempts_count)
    next_attempt = now + timedelta(seconds=delay)
    dummy_cache[block_key] = {"value": next_attempt, "ttl": delay}

    # when & then
    with pytest.raises(ValidationError) as e:
        authenticate_with_throttling(request, EXISTING_EMAIL, INCORRECT_PASSWORD)

    error = e.value
    assert error.code == AccountErrorCode.LOGIN_ATTEMPT_DELAYED.value
    assert str(next_attempt) in error.message

    assert mocked_cache.get(ip_key) == ip_attempts_count
    assert mocked_cache.get(ip_user_key) == ip_user_attempts_count
    assert mocked_cache.get(block_key) == next_attempt


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_race_condition(
    mocked_cache, rf, customer_user, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    next_attempt = now + timedelta(seconds=MIN_DELAY)

    # when
    def login_attempt(*args, **kwargs):
        authenticate_with_throttling(request, EXISTING_EMAIL, INCORRECT_PASSWORD)

    with before_after.before("saleor.account.throttling.add_block", login_attempt):
        with pytest.raises(ValidationError) as e:
            authenticate_with_throttling(request, EXISTING_EMAIL, INCORRECT_PASSWORD)

    # then
    error = e.value
    assert error.code == AccountErrorCode.LOGIN_ATTEMPT_DELAYED.value
    assert str(next_attempt) in error.message

    assert mocked_cache.get(ip_key) == 1
    assert mocked_cache.get(ip_user_key) == 1
    assert mocked_cache.get(block_key) == next_attempt


@freeze_time("2024-05-31 12:00:01")
@patch("saleor.account.throttling.cache")
def test_authenticate_incorrect_credentials_max_attempts(
    mocked_cache,
    rf,
    customer_user,
    setup_mock_for_cache,
    caplog,
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    now = timezone.now()
    caplog.set_level(logging.WARNING)

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state after a couple of login attempts
    ip_attempts_count = 100
    ip_user_attempts_count = 10
    dummy_cache[ip_key] = {"value": ip_attempts_count, "ttl": 100}
    dummy_cache[ip_user_key] = {"value": ip_user_attempts_count, "ttl": 100}
    expected_delay = get_delay_time(ip_attempts_count + 1, ip_user_attempts_count + 1)
    assert expected_delay == MAX_DELAY

    # when
    user = authenticate_with_throttling(request, EXISTING_EMAIL, INCORRECT_PASSWORD)

    # then
    assert not user
    next_attempt = mocked_cache.get(block_key)
    updated_ip_attempts_count = mocked_cache.get(ip_key)
    updated_ip_user_attempts_count = mocked_cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=expected_delay)
    assert updated_ip_attempts_count == ip_attempts_count + 1
    assert updated_ip_user_attempts_count == ip_user_attempts_count + 1
    assert "Unsuccessful logging attempts reached max value." in caplog.text
