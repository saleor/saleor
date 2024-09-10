from typing import Any, Optional
from saleor.core import EventDeliveryStatus
from saleor.core.models import EventDelivery

from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.models import Webhook
from saleor.webhook.transport.utils import WebhookResponse
WebhookEventSyncType


ENABLED_WEBHOOK_EVENT_TYPES = [
    WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
]


# TODO - check - given how this is running in production (gunicorn, uvicorn) does this code NEED
# to be thread safe (in a span of a single process)
class BreakerBoard:
    """
    Base class for breaker board implementations.

    Breaker board serves as single point of entry for different Webhooks from different
    Apps. Basing on the input it checks appropriate circuit breaker state and controls
    webhook execution.
    """

    def __init__(self, func=None):
        self.func = func

    def raise_if_func_is_not_set(self):
        if self.func is None:
            raise RuntimeError("Function not set, breaker board can only observe the circuit breakers state")

    def is_closed(self, app_id: int):
        return True

    def register_failure(self, app_id: int):
        pass

    def register_success(self, app_id: int):
        pass

    def __call__(self, *args, **kwargs) -> tuple[WebhookResponse, Optional[dict[Any, Any]]]:
        self.raise_if_func_is_not_set()

        delivery: EventDelivery = args[0]
        webhook: Webhook = delivery.webhook

        # TODO - change webhook.name to webhook event type (?)
        if webhook.name not in ENABLED_WEBHOOK_EVENT_TYPES:
            return self.func(*args, **kwargs)

        # TODO - ensure app.id is preloaded
        app = webhook.app

        if not self.is_closed(app.id):
            return WebhookResponse(content=""), None

        response, data = self.func(*args, **kwargs)
        if response.status == EventDeliveryStatus.FAILED:
            self.register_failure(app.id)
        else:
            self.register_success(app.id)

        return response, data


# TODO
class RedisBreakerBoard:
    pass
