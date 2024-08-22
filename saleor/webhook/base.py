from collections.abc import Iterable
from typing import Any, Callable, Optional, TypeVar

from django.conf import settings

from ..core.middleware import Requestor
from ..core.utils.events import call_event
from ..permission.enums import BasePermissionEnum
from .models import Webhook


class WebhookBase:
    description: str
    event_type: str
    legacy_manager_func: Optional[str]
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
    def trigger_webhook_async(
        cls,
        subscribable_object: Any,
        requestor: Optional[Requestor],
        webhooks: Optional[Iterable[Webhook]] = None,
        allow_replica: bool = True,
        legacy_data_generator: Optional[Callable] = None,
    ):
        from ..plugins.manager import get_plugins_manager
        from .transport.asynchronous.transport import trigger_webhooks_async
        from .utils import get_webhooks_for_event

        if settings.USE_LEGACY_WEBHOOK_PLUGIN and cls.legacy_manager_func is not None:
            # Trigger webhook via legacy webhook plugin
            manager = get_plugins_manager(allow_replica)
            manager_func = getattr(manager, cls.legacy_manager_func, None)
            if manager_func:
                call_event(manager_func, subscribable_object)
        else:
            # Trigger webhook directly
            if webhooks is None:
                webhooks = get_webhooks_for_event(cls)
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
