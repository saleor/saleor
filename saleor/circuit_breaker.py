import logging
from datetime import datetime

from django.core.cache import cache

from .core import EventDeliveryStatus
from .webhook.event_types import WebhookEventSyncType
from .webhook.transport.utils import WebhookResponse

logger = logging.getLogger(__name__)


CIRCUIT_BREAKER_ENABLED_WEBHOOKS = [
    WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
]
FAILURES_LIMIT_PER_APP = 30
BRAKER_COUNT_WINDOW = 5 * 60  # 5 minutes
BREAKER_COOLDOWN = 10 * 60  # 10 minutes
BASE_CACHE_KEY = "breaker"


def _get_cache_key(app):
    return f"{BASE_CACHE_KEY}:{app.id}"


def _get_age_cache_key(app):
    return f"{BASE_CACHE_KEY}:age:{app.id}"


def _create_age_state(app):
    age_key = _get_age_cache_key(app)
    cache.set(age_key, datetime.now())


def _renew_cache_age_if_expired(app):
    age_key = _get_age_cache_key(app)
    age = cache.get(age_key)
    if not age:
        cache.set(age_key, datetime.now())
    else:
        if (
            age
            and (datetime.now() - age).seconds > BRAKER_COUNT_WINDOW
            and not _breaker_tripped(app)
        ):
            cache.delete(age_key)
            cache.delete(_get_cache_key(app))


def _breaker_tripped(app):
    return cache.get(_get_cache_key(app), 0) >= FAILURES_LIMIT_PER_APP


def breaker_incr(app):
    key = _get_cache_key(app)

    _renew_cache_age_if_expired(app)
    try:
        failure_counter = cache.incr(key)
    except ValueError:
        failure_counter = 1
        cache.add(key, failure_counter)
        _create_age_state(app)

    if failure_counter >= FAILURES_LIMIT_PER_APP:
        if cache._expire_info.get(cache.make_key(key)):
            cache.touch(key, BREAKER_COOLDOWN)
            logger.info(
                "Breaker tripped for app %s. Cooling down for %s seconds.",
                app.name,
                BREAKER_COOLDOWN,
            )


def breaker_sync(func):
    def wrapper(*args, **kwargs):
        delivery = args[0]
        webhook = delivery.webhook
        if webhook.name not in CIRCUIT_BREAKER_ENABLED_WEBHOOKS:
            return func(*args, **kwargs)

        app = webhook.app
        if _breaker_tripped(app):
            return WebhookResponse(content=""), None
        response, data = func(*args, **kwargs)
        if response.status == EventDeliveryStatus.FAILED:
            breaker_incr(app)
        return response, data

    return wrapper
