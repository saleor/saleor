from collections.abc import Iterable
from functools import partial
from typing import Any, Callable, Optional, TypeVar

from ..core.middleware import Requestor
from ..core.utils.events import call_event
from ..permission.enums import BasePermissionEnum
from .models import Webhook


class WebhookBase:
    description: str
    event_type: str
    name: str
    permission: BasePermissionEnum
    subscription_type: str


class SyncWebhookBase(WebhookBase):
    # For now this class is only use to distinguish between sync and async webhooks.
    # When migrating more webhooks to the new approach, this class could implement
    # generic function to trigger sync webhooks.
    pass


class AsyncWebhookBase(WebhookBase):
    @classmethod
    def legacy_payload_func(cls) -> Optional[Callable]:
        return None

    @classmethod
    def trigger_webhook_async(
        cls,
        subscribable_object: Any,
        requestor: Optional[Requestor] = None,
        webhooks: Optional[Iterable[Webhook]] = None,
        allow_replica: bool = True,
    ):
        from .transport.asynchronous.transport import trigger_webhooks_async
        from .utils import get_webhooks_for_event

        if webhooks is None:
            webhooks = get_webhooks_for_event(cls)

        legacy_data_generator = None
        if legacy_payload_func := cls.legacy_payload_func():
            legacy_data_generator = partial(
                legacy_payload_func,
                subscribable_object=subscribable_object,
                requestor=requestor,
            )

        call_event(
            trigger_webhooks_async,
            data=None,
            event_type=cls,
            webhooks=webhooks,
            subscribable_object=subscribable_object,
            requestor=requestor,
            legacy_data_generator=legacy_data_generator,
            allow_replica=allow_replica,
        )


WebhookBaseType = TypeVar("WebhookBaseType", bound=WebhookBase)
AsyncWebhookBaseType = TypeVar("AsyncWebhookBaseType", bound=AsyncWebhookBase)
SyncWebhookBaseType = TypeVar("SyncWebhookBaseType", bound=SyncWebhookBase)
