import logging
from typing import TYPE_CHECKING, Any, Union

from django.conf import settings
from promise import Promise
from pydantic import ValidationError

from ...shipping.interface import ShippingMethodData
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.payloads import generate_checkout_payload
from ...webhook.response_schemas.shipping import ListShippingMethodsSchema
from ...webhook.transport.synchronous.transport import trigger_webhook_sync_promise
from ...webhook.utils import get_webhooks_for_event
from ..models import Checkout

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App

logger = logging.getLogger(__name__)


def list_shipping_methods_for_checkout(
    checkout: "Checkout",
    built_in_shipping_methods: list["ShippingMethodData"],
    allow_replica: bool,
    requestor: Union["App", "User", None],
) -> Promise[list["ShippingMethodData"]]:
    methods: list[ShippingMethodData] = []
    event_type = WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    webhooks = get_webhooks_for_event(event_type)
    if not webhooks:
        return Promise.resolve(methods)

    promised_responses = []
    payload = generate_checkout_payload(checkout, requestor)
    for webhook in webhooks:
        promised_responses.append(
            trigger_webhook_sync_promise(
                event_type=event_type,
                static_payload=payload,
                webhook=webhook,
                allow_replica=allow_replica,
                subscribable_object=(checkout, built_in_shipping_methods),
                timeout=settings.WEBHOOK_SYNC_TIMEOUT,
                requestor=requestor,
            )
        )

    def process_responses(responses: list[Any]):
        for response_data, webhook in zip(responses, webhooks, strict=True):
            if response_data:
                shipping_methods = _parse_list_shipping_methods_response(
                    response_data, webhook.app, checkout.currency
                )
                methods.extend(shipping_methods)
        return [
            method for method in methods if method.price.currency == checkout.currency
        ]

    return Promise.all(promised_responses).then(process_responses)


def _parse_list_shipping_methods_response(
    response_data: Any, app: "App", object_currency: str
) -> list["ShippingMethodData"]:
    try:
        list_shipping_method_model = ListShippingMethodsSchema.model_validate(
            response_data,
            context={
                "app": app,
                "currency": object_currency,
                "custom_message": "Skipping invalid shipping method (ListShippingMethodsSchema)",
            },
        )
    except ValidationError:
        logger.warning("Skipping invalid shipping method response: %s", response_data)
        return []
    return [
        ShippingMethodData(
            id=shipping_method.id,
            name=shipping_method.name,
            price=shipping_method.price,
            maximum_delivery_days=shipping_method.maximum_delivery_days,
            minimum_delivery_days=shipping_method.minimum_delivery_days,
            description=shipping_method.description,
            metadata=shipping_method.metadata,
            private_metadata=shipping_method.private_metadata,
        )
        for shipping_method in list_shipping_method_model.root
    ]
