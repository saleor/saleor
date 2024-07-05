import logging
from datetime import timedelta
from math import ceil
from typing import Optional

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..core.utils import get_client_ip
from . import models
from .error_codes import AccountErrorCode
from .utils import retrieve_user_by_email

MIN_DELAY = 1
MAX_DELAY = 3600
ATTEMPT_COUNTER_EXPIRE_TIME = 7200

logger = logging.getLogger(__name__)


def authenticate_with_throttling(request, email, password) -> Optional[models.User]:
    ip = get_client_ip(request)
    if not ip:
        logger.warning("Unknown request's IP address.")
        raise ValidationError(
            "Can't indentify requester IP address.",
            code=AccountErrorCode.UNKNOWN_IP_ADDRESS.value,
        )

    ip_key = get_cache_key_failed_ip(ip)
    block_key = get_cache_key_blocked_ip(ip)

    # block the IP address before the next attempt to prevent concurrent requests
    if add_block(block_key, MIN_DELAY) is False:
        next_attempt_time = cache.get(block_key) or timezone.now() + timedelta(
            seconds=MIN_DELAY
        )
        raise ValidationError(
            f"Logging has been suspended till {next_attempt_time} due to too many "
            f"logging attempts originating from the same IP address.",
            code=AccountErrorCode.LOGIN_ATTEMPT_DELAYED.value,
        )

    # retrieve user from credentials
    ip_user_attempts_count = 0
    if user := retrieve_user_by_email(email):
        ip_user_key = get_cache_key_failed_ip_with_user(ip, user.pk)
        if user.check_password(password):
            # clear cache entries when login successful
            clear_cache([ip_key, ip_user_key, block_key])
            return user

        else:
            # increment failed attempt for known user
            ip_user_attempts_count = increment_attempt(ip_user_key)

    # increment failed attempt for whatever user
    ip_attempts_count = increment_attempt(ip_key)

    # calculate next allowed login attempt time and block the IP till the time
    delay = get_delay_time(ip_attempts_count, ip_user_attempts_count)
    if delay == MAX_DELAY:
        logger.warning("Unsuccessful logging attempts reached max value.")
    override_block(block_key, delay)

    return None


def get_cache_key_failed_ip(ip: str) -> str:
    return f"login:fail:ip:{ip}"


def get_cache_key_failed_ip_with_user(ip: str, user_id) -> str:
    return f"login:fail:ip:{ip}:user:{user_id}"


def get_cache_key_blocked_ip(ip: str) -> str:
    return f"login:block:ip:{ip}"


def clear_cache(keys: list[str]):
    for key in keys:
        cache.delete(key)


def get_delay_time(ip_attempts_count: int, ip_user_attempts_count: int) -> int:
    """Calculate next login attempt delay, based on number of attempts.

    Delay is incremented by the power of 2.

    We distinguish two cases:
    - Case "A": many failed logins for the same IP address, no matters the username
    provided, to prevent credential stuffing
    - Case "B": many failed logins for the same IP address and same existing username,
    to prevent brute-forcing

    For case "A" we increment delay time every 10 attempts. It means delay will be
    1sec for attempts 1-10, 2sec for attempts 11-20, 4 sec for attempts 21-30 and so on.

    For case "B" we increment delay time every single attempt. It means delay will be
    1sec after attempt 1, 2sec after attempt 2, 4sec after attempt 3 and so on.
    """
    ip_delay = 0
    if ip_attempts_count > 0:
        ip_delay = (
            2 ** (ceil(ip_attempts_count / 10) - 1)
            if ip_attempts_count < 100
            else MAX_DELAY
        )

    ip_user_delay = 0
    if ip_user_attempts_count > 0:
        ip_user_delay = (
            2 ** (ip_user_attempts_count - 1)
            if ip_user_attempts_count < 10
            else MAX_DELAY
        )

    return max(ip_delay, ip_user_delay, MIN_DELAY)


def override_block(block_key: str, time_delta: int):
    next_attempt_time = timezone.now() + timedelta(seconds=time_delta)
    cache.set(block_key, next_attempt_time, timeout=time_delta)


def add_block(block_key: str, time_delta: int) -> bool:
    next_attempt_time = timezone.now() + timedelta(seconds=time_delta)
    return cache.add(block_key, next_attempt_time, timeout=time_delta)


def increment_attempt(key: str) -> int:
    # `cache.add` returns False and does nothing, when key already exists
    if not cache.add(key, 1, timeout=ATTEMPT_COUNTER_EXPIRE_TIME):
        return cache.incr(key, 1)
    return 1
