import logging
import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from saleor.webhook.event_types import WebhookEventSyncType

if TYPE_CHECKING:
    from ...webhook.models import Webhook


logger = logging.getLogger(__name__)


# TODO - check - given how this is running in production (gunicorn, uvicorn) does this code NEED
# to be thread safe (in a span of a single process)
class BreakerBoard:
    """Base class for breaker board implementations.

    Breaker board serves as single point of entry for different Webhooks from different
    Apps. Basing on the input it checks appropriate circuit breaker state and controls
    webhook execution.
    """

    def __init__(
        self,
        storage,
        failure_threshold: int,
        failure_min_count: int,
        cooldown_seconds: int,
        ttl_seconds: int,
    ):
        self.validate_sync_events()
        self.storage = storage
        self.failure_threshold = failure_threshold
        self.failure_min_count = failure_min_count
        self.cooldown_seconds = cooldown_seconds
        self.ttl_seconds = ttl_seconds

    def validate_sync_events(self):
        if settings.BREAKER_BOARD_SYNC_EVENTS == [""]:
            raise ImproperlyConfigured("BREAKER_BOARD_SYNC_EVENTS cannot be empty.")
        for event in settings.BREAKER_BOARD_SYNC_EVENTS:
            if not WebhookEventSyncType.EVENT_MAP.get(event):
                raise ImproperlyConfigured(
                    f'Event "{event}" is not supported by circuit breaker.'
                )

    def is_closed(self, app_id: int):
        return self.storage.last_open(app_id) < (time.time() - self.cooldown_seconds)

    def register_error(self, app_id: int):
        errors = self.storage.register_event_returning_count(
            app_id, "error", self.ttl_seconds
        )
        total = self.storage.register_event_returning_count(
            app_id, "total", self.ttl_seconds
        )

        if total < self.failure_min_count:
            return

        if (errors / total) * 100 >= self.failure_threshold:
            self.storage.update_open(app_id, int(time.time()))
            logger.info(
                "[App ID: %r] Circuit breaker tripped, cooldown is %r [seconds].",
                app_id,
                self.cooldown_seconds,
            )

    def register_success(self, app_id: int):
        self.storage.register_event_returning_count(app_id, "total", self.ttl_seconds)

        last_open = self.storage.last_open(app_id)
        if last_open == 0:
            return

        if last_open < (time.time() - self.cooldown_seconds):
            logger.info("[App ID: %r] Circuit breaker recovered.", app_id)
            self.storage.update_open(app_id, 0)

    def __call__(self, func):
        def inner(*args, **kwargs):
            event_type: str = args[0]
            webhook: Webhook = args[2]

            if event_type not in settings.BREAKER_BOARD_SYNC_EVENTS:
                return func(*args, **kwargs)

            app_id = webhook.app.id
            if not self.is_closed(app_id):
                return None

            response = func(*args, **kwargs)
            if response is None:
                self.register_error(app_id)
            else:
                self.register_success(app_id)

            return response

        inner.__wrapped__ = func  # type: ignore[attr-defined]

        return inner


def initialize_breaker_board():
    if not settings.ENABLE_BREAKER_BOARD:
        return None

    storage_class = import_string(settings.BREAKER_BOARD_STORAGE_CLASS)  # type: ignore[arg-type]
    return BreakerBoard(
        storage=storage_class(),
        failure_threshold=settings.BREAKER_BOARD_FAILURE_THRESHOLD_PERCENTAGE,
        failure_min_count=settings.BREAKER_BOARD_FAILURE_MIN_COUNT,
        cooldown_seconds=settings.BREAKER_BOARD_COOLDOWN_SECONDS,
        ttl_seconds=settings.BREAKER_BOARD_TTL_SECONDS,
    )
