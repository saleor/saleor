import json
import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

from django.conf import settings
from django.db.models import QuerySet
from promise import Promise
from pydantic import ValidationError

from ...core.db.connection import allow_writer
from ...core.utils.json_serializer import CustomJsonEncoder
from ...shipping.interface import ShippingMethodData
from ...webhook import traced_payload_generator
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.models import Webhook
from ...webhook.payloads import (
    generate_order_payload,
    generate_payload_for_shipping_method,
)
from ...webhook.response_schemas.shipping import (
    ExcludedShippingMethodSchema,
    FilterShippingMethodsSchema,
)
from ...webhook.transport.synchronous.transport import (
    trigger_webhook_sync_promise_if_not_cached,
)
from ...webhook.utils import get_webhooks_for_event

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App
    from ...checkout.models import Checkout
    from ...order.models import Order

CACHE_EXCLUDED_SHIPPING_TIME = 60 * 3

logger = logging.getLogger(__name__)


@dataclass
class ExcludedShippingMethod:
    id: str
    reason: str | None


@allow_writer()
@traced_payload_generator
def generate_excluded_shipping_methods_for_order_payload(
    order: "Order",
    available_shipping_methods: list[ShippingMethodData],
):
    order_data = json.loads(generate_order_payload(order))[0]
    payload = {
        "order": order_data,
        "shipping_methods": [
            generate_payload_for_shipping_method(shipping_method)
            for shipping_method in available_shipping_methods
        ],
    }
    return json.dumps(payload, cls=CustomJsonEncoder)


def excluded_shipping_methods_for_order(
    order: "Order",
    available_shipping_methods: list["ShippingMethodData"],
    allow_replica: bool,
    requestor: Union["App", "User", None],
) -> Promise[list[ExcludedShippingMethod]]:
    if not available_shipping_methods:
        return Promise.resolve([])

    generate_function = generate_excluded_shipping_methods_for_order_payload
    payload_fun = lambda: generate_function(  # noqa: E731
        order,
        available_shipping_methods,
    )
    return _get_excluded_shipping_data(
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        payload_fun=payload_fun,
        subscribable_object=(order, available_shipping_methods),
        allow_replica=allow_replica,
        requestor=requestor,
    )


def _get_cache_data_for_exclude_shipping_methods(payload: str) -> dict:
    payload_dict = json.loads(payload)
    source_object = payload_dict.get("checkout", payload_dict.get("order", {}))

    # drop fields that change between requests but are not relevant for cache key
    source_object.pop("last_change", None)
    source_object.pop("meta", None)
    source_object.pop("shipping_method", None)
    return payload_dict


def _get_excluded_shipping_methods_or_fetch(
    webhooks: QuerySet,
    event_type: str,
    payload: str,
    subscribable_object: (
        tuple[Union["Order", "Checkout"], list["ShippingMethodData"]] | None
    ),
    allow_replica: bool,
    requestor: Union["App", "User", None],
) -> Promise[dict[str, list[ExcludedShippingMethod]]]:
    """Return data of all excluded shipping methods.

    The data will be fetched from the cache. If missing it will fetch it from all
    defined webhooks by calling a request to each of them one by one.
    """
    cache_data = _get_cache_data_for_exclude_shipping_methods(payload)
    # Gather responses from webhooks
    promised_responses = []

    for webhook in webhooks:
        promised_responses.append(
            trigger_webhook_sync_promise_if_not_cached(
                event_type=event_type,
                payload=payload,
                webhook=webhook,
                cache_data=cache_data,
                allow_replica=allow_replica,
                subscribable_object=subscribable_object,
                request_timeout=settings.WEBHOOK_SYNC_TIMEOUT,
                cache_timeout=CACHE_EXCLUDED_SHIPPING_TIME,
                requestor=requestor,
            )
        )

    def process_responses(
        responses: list[Any],
    ) -> dict[str, list[ExcludedShippingMethod]]:
        excluded_methods: list[ExcludedShippingMethodSchema] = []
        for response_data, webhook in zip(responses, webhooks, strict=True):
            if response_data and isinstance(response_data, dict):
                excluded_methods.extend(
                    _get_excluded_shipping_methods_from_response(response_data, webhook)
                )
        return _parse_excluded_shipping_methods(excluded_methods)

    return Promise.all(promised_responses).then(process_responses)


def _get_excluded_shipping_data(
    event_type: str,
    payload_fun: Callable[[], str],
    subscribable_object: (
        tuple[Union["Order", "Checkout"], list["ShippingMethodData"]] | None
    ),
    allow_replica: bool,
    requestor: Union["App", "User", None],
) -> Promise[list[ExcludedShippingMethod]]:
    """Exclude not allowed shipping methods by sync webhook.

    Fetch excluded shipping methods from sync webhooks and return them as a list of
    excluded shipping methods.
    The function uses a cache_key to reduce the number of
    requests which we call to the external APIs. In case when we have the same payload
    in a cache as we're going to send now, we will skip an additional request and use
    the response fetched from cache.
    The function will fetch the payload only in the case that we have any defined
    webhook.
    """
    webhooks = get_webhooks_for_event(event_type)
    if webhooks:
        payload = payload_fun()
        promised_excluded_methods_map = _get_excluded_shipping_methods_or_fetch(
            webhooks,
            event_type,
            payload,
            subscribable_object,
            allow_replica,
            requestor,
        )
    else:
        promised_excluded_methods_map = Promise.resolve({})

    def merge_excluded_methods_map(
        excluded_methods_map: dict[str, list[ExcludedShippingMethod]],
    ) -> list[ExcludedShippingMethod]:
        # Return a list of excluded methods, unique by id
        excluded_methods = []
        for method_id, methods in excluded_methods_map.items():
            reason = None
            if reasons := [m.reason for m in methods if m.reason]:
                reason = " ".join(reasons)
            excluded_methods.append(ExcludedShippingMethod(id=method_id, reason=reason))
        return excluded_methods

    return promised_excluded_methods_map.then(merge_excluded_methods_map)


def _get_excluded_shipping_methods_from_response(
    response_data: dict,
    webhook: "Webhook",
) -> list[ExcludedShippingMethodSchema]:
    excluded_methods = []
    try:
        filter_methods_schema = FilterShippingMethodsSchema.model_validate(
            response_data,
            context={
                "custom_message": "Skipping invalid shipping method (FilterShippingMethodsSchema)"
            },
        )
        excluded_methods.extend(filter_methods_schema.excluded_methods)
    except ValidationError:
        logger.warning(
            "Skipping invalid response from app %s: %s",
            str(webhook.app.identifier),
            response_data,
        )
    return excluded_methods


def _parse_excluded_shipping_methods(
    excluded_methods: list[ExcludedShippingMethodSchema],
) -> dict[str, list[ExcludedShippingMethod]]:
    """Prepare method_id to excluded methods map."""
    excluded_methods_map = defaultdict(list)
    for excluded_method in excluded_methods:
        method_id = excluded_method.id
        reason = excluded_method.reason or ""
        excluded_methods_map[method_id].append(
            ExcludedShippingMethod(id=method_id, reason=reason)
        )
    return excluded_methods_map
