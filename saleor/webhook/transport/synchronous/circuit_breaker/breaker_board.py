import time
from typing import TYPE_CHECKING

from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.transport.synchronous.circuit_breaker.storage import (
    Storage,
)
from saleor.webhook.transport.utils import WebhookResponse

if TYPE_CHECKING:
    from .....webhook.models import Webhook


# TODO - check - given how this is running in production (gunicorn, uvicorn) does this code NEED
# to be thread safe (in a span of a single process)
class BreakerBoard:
    """Base class for breaker board implementations.

    Breaker board serves as single point of entry for different Webhooks from different
    Apps. Basing on the input it checks appropriate circuit breaker state and controls
    webhook execution.
    """

    def __init__(self, storage: Storage, failure_threshold: int):
        self.storage = storage

        # TODO - make everything below configurable
        self.failure_threshold = failure_threshold
        self.webhook_event_types = [
            WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
        ]
        self.cooldown_seconds = 5 * 60  # 5 minutes
        self.ttl = 10 * 60  # 10 minutes

    def is_closed(self, app_id: int):
        # TODO - cache last open to optimize?
        return self.storage.last_open(app_id) < (time.time() - self.cooldown_seconds)

    def register_error(self, app_id: int):
        errors = self.storage.register_event_returning_count(
            f"{0}-{1}".format(app_id, "error"), self.ttl
        )

        if errors >= self.failure_threshold:
            self.storage.update_open(app_id, int(time.time()))

    def register_success(self, app_id: int):
        self.storage.register_event_returning_count(
            f"{0}-{1}".format(app_id, "total"), self.ttl
        )

        last_open = self.storage.last_open(app_id)
        if last_open == 0:
            return

        if last_open < (time.time() - self.cooldown_seconds):
            self.storage.update_open(app_id, 0)

    def __call__(self, func):
        def inner(*args, **kwargs):
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
