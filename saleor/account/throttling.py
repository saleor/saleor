from datetime import timedelta
from math import ceil
from typing import Optional

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.utils import timezone

from ..graphql.core import ResolveInfo
from . import models
from .error_codes import AccountErrorCode
from .utils import retrieve_user_by_email

MIN_DELAY = 1
MAX_DELAY = 3600
ATTEMPT_COUNTER_EXPIRE_TIME = 7200


def authenticate_with_throttling(
    info: ResolveInfo, email, password
) -> Optional[models.User]:
    ip = get_ip_address(info)
    if not ip:
        # TODO zedzior
        pass

    ip_key = get_cache_key_failed_ip(ip)
    block_key = get_cache_key_blocked_ip(ip)

    # block the IP address before the next attempt to prevent concurrent requests
    if add_block(block_key, MIN_DELAY) is False:
        next_attempt_time = cache.get(block_key) or MIN_DELAY
        raise ValidationError(
            {
                "email": ValidationError(
                    f"Due to too many failed authentication attempts, "
                    f"logging has been suspended till {next_attempt_time}.",
                    code=AccountErrorCode.LOGIN_ATTEMPT_DELAYED.value,
                )
            }
        )

    # retrieve user from credential
    ip_user_attempts_count = MIN_DELAY
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
    override_block(block_key, delay)

    return None


def is_ip_address_valid(ip):
    if not ip:
        return False
    try:
        validate_ipv46_address(ip)
        return True
    except ValidationError:
        return False


def get_ip_address(info: ResolveInfo) -> str:
    proxy_address = info.context.META.get("HTTP_X_FORWARDED_FOR", "").strip()
    remote_address = info.context.META.get("REMOTE_ADDR", "").strip()
    ip = proxy_address or remote_address
    if ip and is_ip_address_valid(ip):
        return ip
    # TODO zedzior
    return ""


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
    ip_delay = (
        2 ^ (ceil(ip_attempts_count / 10) - 1) if ip_attempts_count < 100 else MAX_DELAY
    )
    ip_user_delay = (
        2 ^ (ip_attempts_count - 1) if ip_user_attempts_count < 10 else MAX_DELAY
    )
    return max(ip_delay, ip_user_delay)


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
