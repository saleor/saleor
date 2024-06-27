from datetime import timedelta

import before_after
import pytest
from django.core.cache import cache
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
def test_authenticate_successful_first_attempt(rf, customer_user):
    # given
    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # when
    user = authenticate_with_throttling(request, EXISTING_EMAIL, CORRECT_PASSWORD)

    # then
    assert user
    assert cache.get(block_key) is None
    assert cache.get(ip_key) is None
    assert cache.get(ip_user_key) is None


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_successful_subsequent_attempt(rf, customer_user):
    """Make sure cache is cleared after successful login."""
    # given
    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state after a couple of login attempts
    cache.set(ip_key, 21, timeout=100)
    cache.set(ip_user_key, 7, timeout=100)

    # when
    user = authenticate_with_throttling(request, EXISTING_EMAIL, CORRECT_PASSWORD)

    # then
    assert user
    assert cache.get(block_key) is None
    assert cache.get(ip_key) is None
    assert cache.get(ip_user_key) is None


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_incorrect_password_non_existing_email_first_attempt(
    rf,
    customer_user,
):
    # given
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
    next_attempt = cache.get(block_key)
    ip_attempts_count = cache.get(ip_key)
    ip_user_attempts_count = cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=MIN_DELAY)
    assert ip_attempts_count == 1
    assert ip_user_attempts_count is None


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_incorrect_password_non_existing_email_subsequent_attempt(
    rf,
    customer_user,
):
    # given
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state after a couple of login attempts
    ip_attempts_count = 21
    cache.set(ip_key, ip_attempts_count, timeout=100)
    expected_delay = get_delay_time(ip_attempts_count + 1, 0)

    # when
    user = authenticate_with_throttling(request, NON_EXISTING_EMAIL, INCORRECT_PASSWORD)

    # then
    assert not user
    next_attempt = cache.get(block_key)
    updated_ip_attempts_count = cache.get(ip_key)
    ip_user_attempts_count = cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=expected_delay)
    assert updated_ip_attempts_count == ip_attempts_count + 1
    assert ip_user_attempts_count is None


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_incorrect_password_existing_email_first_attempt(
    rf,
    customer_user,
):
    # given
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
    next_attempt = cache.get(block_key)
    ip_attempts_count = cache.get(ip_key)
    ip_user_attempts_count = cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=MIN_DELAY)
    assert ip_attempts_count == 1
    assert ip_user_attempts_count == 1


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_incorrect_password_existing_email_subsequent_attempt(
    rf,
    customer_user,
):
    # given
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state after a couple of login attempts
    ip_attempts_count = 21
    ip_user_attempts_count = 5
    cache.set(ip_key, ip_attempts_count, timeout=100)
    cache.set(ip_user_key, ip_user_attempts_count, timeout=100)
    expected_delay = get_delay_time(ip_attempts_count + 1, ip_user_attempts_count + 1)

    # when
    user = authenticate_with_throttling(request, EXISTING_EMAIL, INCORRECT_PASSWORD)

    # then
    assert not user
    next_attempt = cache.get(block_key)
    updated_ip_attempts_count = cache.get(ip_key)
    updated_ip_user_attempts_count = cache.get(ip_user_key)

    assert next_attempt == now + timedelta(seconds=expected_delay)
    assert updated_ip_attempts_count == ip_attempts_count + 1
    assert updated_ip_user_attempts_count == ip_user_attempts_count + 1


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_unidentified_ip_address(rf, customer_user):
    # given
    request = rf.request(HTTP_X_FORWARDED_FOR="", REMOTE_ADDR="")

    # when & then
    with pytest.raises(ValidationError) as e:
        authenticate_with_throttling(request, EXISTING_EMAIL, CORRECT_PASSWORD)

    error = e.value.error_dict["email"][0]
    assert error.code == AccountErrorCode.UNKNOWN_IP_ADDRESS.value


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_login_attempt_delayed(rf, customer_user):
    # given
    now = timezone.now()

    ip = "123.123.123.123"
    request = rf.request(HTTP_X_FORWARDED_FOR=ip)

    block_key = get_cache_key_blocked_ip(ip)
    ip_key = get_cache_key_failed_ip(ip)
    ip_user_key = get_cache_key_failed_ip_with_user(ip, customer_user.id)

    # imitate cache state when login is temporarily blocked
    ip_attempts_count = 21
    ip_user_attempts_count = 5
    cache.set(ip_key, ip_attempts_count, timeout=100)
    cache.set(ip_user_key, ip_user_attempts_count, timeout=100)
    delay = get_delay_time(ip_attempts_count, ip_user_attempts_count)
    next_attempt = now + timedelta(seconds=delay)
    cache.set(block_key, next_attempt)

    # when & then
    with pytest.raises(ValidationError) as e:
        authenticate_with_throttling(request, EXISTING_EMAIL, INCORRECT_PASSWORD)

    error = e.value.error_dict["email"][0]
    assert error.code == AccountErrorCode.LOGIN_ATTEMPT_DELAYED.value
    assert str(next_attempt) in error.message

    assert cache.get(ip_key) == ip_attempts_count
    assert cache.get(ip_user_key) == ip_user_attempts_count
    assert cache.get(block_key) == next_attempt


@freeze_time("2024-05-31 12:00:01")
def test_authenticate_race_condition(rf, customer_user):
    # given
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
    error = e.value.error_dict["email"][0]
    assert error.code == AccountErrorCode.LOGIN_ATTEMPT_DELAYED.value
    assert str(next_attempt) in error.message

    assert cache.get(ip_key) == 1
    assert cache.get(ip_user_key) == 1
    assert cache.get(block_key) == next_attempt
