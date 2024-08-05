from collections.abc import Iterable
from typing import Any, Optional, TypeVar, Union

from django.utils.module_loading import import_string

from ..account.models import User
from ..app.models import App
from ..permission.enums import BasePermissionEnum
from .models import Webhook


class WebhookSpec:
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
        legacy_payload_generator: Any = None,
    ):
        from .transport.asynchronous.transport import trigger_webhooks_async
        from .utils import get_webhooks_for_event

        if webhooks is None:
            webhooks = get_webhooks_for_event(cls)

        if webhooks:
            # TODO: add support for legacy_payload_generator
            # product_data_generator = partial(generate_product_payload, product, requestor)
            trigger_webhooks_async(
                None,
                cls,
                webhooks,
                subscribable_object,
                requestor,
                legacy_data_generator=None,
                allow_replica=allow_replica,
            )


WebhookSpecType = TypeVar("WebhookSpecType", bound=WebhookSpec)


def register(webhook_spec: type[WebhookSpecType]):
    from ..graphql.webhook.subscription_types import WEBHOOK_TYPES_MAP

    # Register webhook subscription type
    WEBHOOK_TYPES_MAP[webhook_spec.event_type] = import_string(
        webhook_spec.subscription_type
    )
