from collections.abc import Iterable
from typing import Any, Callable, Optional, TypeVar, Union

from django.utils.module_loading import import_string

from ..account.models import User
from ..app.models import App
from ..permission.enums import BasePermissionEnum
from .models import Webhook


class WebhookBase:
    description: str
    event_type: str
    name: str
    permission: BasePermissionEnum
    subscription_type: str

    @classmethod
    def call_webhook(
        cls,
        subscribable_object: Any,
        requestor: Union[User, App],
        webhooks: Optional[Iterable[Webhook]] = None,
        allow_replica: bool = True,
        legacy_data_generator: Optional[Callable] = None,
    ):
        from .transport.asynchronous.transport import trigger_webhooks_async
        from .utils import get_webhooks_for_event

        if webhooks is None:
            webhooks = get_webhooks_for_event(cls)

        if webhooks:
            trigger_webhooks_async(
                None,
                cls,
                webhooks,
                subscribable_object,
                requestor,
                legacy_data_generator=legacy_data_generator,
                allow_replica=allow_replica,
            )


WebhookBaseType = TypeVar("WebhookBaseType", bound=WebhookBase)


def register(webhook_spec: type[WebhookBaseType]):
    from ..graphql.webhook.subscription_types import WEBHOOK_TYPES_MAP

    # Register webhook subscription type
    WEBHOOK_TYPES_MAP[webhook_spec.event_type] = import_string(
        webhook_spec.subscription_type
    )
