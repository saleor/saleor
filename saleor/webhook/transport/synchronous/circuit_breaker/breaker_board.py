import logging
import time
from typing import TYPE_CHECKING, Optional

from django.conf import settings

from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.transport.synchronous.circuit_breaker.const import BreakerMode
from saleor.webhook.transport.synchronous.circuit_breaker.storage import (
    InMemoryStorage,
    Storage,
)
from saleor.webhook.transport.utils import WebhookResponse

if TYPE_CHECKING:
    from .....webhook.models import Webhook

logger = logging.getLogger(__name__)


# TODO - check - given how this is running in production (gunicorn, uvicorn) does this code NEED
# to be thread safe (in a span of a single process)
class BreakerBoard:
    """Base class for breaker board implementations.

    Breaker board serves as single point of entry for different Webhooks from different
    Apps. Basing on the input it checks appropriate circuit breaker state and controls
    webhook execution.
    """

    def configure(
        self,
        storage: Storage,
        mode: str,
        failure_threshold: float,
        cooldown_seconds: int,
        ttl: int,
    ):
        self.failure_threshold = failure_threshold or settings.BREAKER_FAILURE_THRESHOLD
        self.cooldown_seconds = cooldown_seconds or settings.BREAKER_COOLDOWN
        self.ttl = ttl or settings.BREAKER_TTL
        if mode == BreakerMode.FIXED and self.failure_threshold < 1:
            logger.info("Circuit breaker threshold invalid.")
            self.mode = BreakerMode.NONE
            return
        elif mode == BreakerMode.PERCENTAGE and (
            self.failure_threshold < 1 or self.failure_threshold > 99
        ):
            logger.info("Circuit breaker threshold invalid.")
            self.mode = BreakerMode.NONE
            return
        self.storage = storage or InMemoryStorage()
        self.mode = mode
        if self.cooldown_seconds < 1 or self.failure_threshold < 1 or self.ttl < 1:
            logger.info("Circuit breaker configuration invalid.")
            self.mode = BreakerMode.NONE

    def __init__(
        self,
        storage: Optional[Storage] = None,
        mode: Optional[str] = None,
        failure_threshold: Optional[float] = None,
        cooldown_seconds: Optional[int] = None,
        ttl: Optional[int] = None,
    ):
        self.mode = mode or settings.BREAKER_MODE
        if (
            not self.mode
            or self.mode == BreakerMode.NONE
            or self.mode not in BreakerMode.OPTIONS
        ):
            self.mode = BreakerMode.NONE
            logger.info("Circuit breaker feature is disabled.")
            return

        # TODO - make configurable or set to proper static list of events
        self.webhook_event_types = [
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
        ]

        self.configure(storage, self.mode, failure_threshold, cooldown_seconds, ttl)

    def is_closed(self, app_id: int):
        # TODO - cache last open to optimize?
        return self.storage.last_open(app_id) < (time.time() - self.cooldown_seconds)

    def register_error(self, app_id: int):
        errors = self.storage.register_event_returning_count(
            f"{0}-{1}".format(app_id, "error"), self.ttl
        )

        open = False
        if self.mode == BreakerMode.FIXED and errors >= self.failure_threshold:
            open = True
        elif self.mode == BreakerMode.PERCENTAGE:
            total = self.storage.get_event_count("success") + errors
            if errors * 100 / total >= self.failure_threshold:
                open = True

        if open:
            logger.warning(f"Circuit breaker tripped for an app with id {app_id}.")
            self.storage.update_open(app_id, int(time.time()))

    def register_success(self, app_id: int):
        self.storage.register_event_returning_count(
            f"{0}-{1}".format(app_id, "success"), self.ttl
        )

        last_open = self.storage.last_open(app_id)
        if last_open == 0:
            return

        if last_open < (time.time() - self.cooldown_seconds):
            self.storage.update_open(app_id, 0)

    def __call__(self, func):
        def inner(*args, **kwargs):
            if self.mode == BreakerMode.NONE:
                return func(*args, **kwargs)

            event_type: str = args[0]
            webhook: Webhook = args[2]

            if event_type not in self.webhook_event_types:
                return func(*args, **kwargs)

            # TODO - ensure webhook and app are preloaded
            app = webhook.app

            if not self.is_closed(app.id):
                return WebhookResponse(content=""), None

            response = func(*args, **kwargs)
            if response is None:
                self.register_error(app.id)
            else:
                self.register_success(app.id)

            return response

        return inner
