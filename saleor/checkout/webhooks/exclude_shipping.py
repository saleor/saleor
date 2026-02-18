import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Union

from django.conf import settings
from django.db.models import QuerySet
from pydantic import ValidationError

from ...app.models import App
from ...core.db.connection import allow_writer
from ...core.utils.json_serializer import CustomJsonEncoder
from ...graphql.webhook.utils import get_pregenerated_subscription_payload
from ...shipping.interface import ExcludedShippingMethod, ShippingMethodData
from ...webhook import traced_payload_generator
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.models import Webhook
from ...webhook.payloads import (
    generate_checkout_payload,
)
from ...webhook.response_schemas.shipping import (
    ExcludedShippingMethodSchema,
    FilterShippingMethodsSchema,
)
from ...webhook.transport.synchronous.transport import (
    trigger_webhook_sync_if_not_cached,
)
from ...webhook.utils import get_webhooks_for_event
from ..models import Checkout

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App

logger = logging.getLogger(__name__)

CACHE_EXCLUDED_SHIPPING_TIME = 60 * 3


def excluded_shipping_methods_for_checkout(
    checkout: "Checkout",
    available_shipping_methods: list["ShippingMethodData"],
    allow_replica: bool,
    requestor: Union["App", "User", None],
    pregenerated_subscription_payloads: dict | None = None,
) -> list[ExcludedShippingMethod]:
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    if not available_shipping_methods:
        return []

    generate_function = _generate_excluded_shipping_methods_for_checkout_payload
    payload_function = lambda: generate_function(  # noqa: E731
        checkout,
        available_shipping_methods,
    )
    return _get_excluded_shipping_data(
        event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        payload_fun=payload_function,
        subscribable_object=(checkout, available_shipping_methods),
        allow_replica=allow_replica,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        requestor=requestor,
    )


def _generate_payload_for_shipping_method(method: ShippingMethodData):
    payload = {
        "id": method.graphql_id,
        "price": method.price.amount,
        "currency": method.price.currency,
        "name": method.name,
        "maximum_order_weight": method.maximum_order_weight,
        "minimum_order_weight": method.minimum_order_weight,
        "maximum_delivery_days": method.maximum_delivery_days,
        "minimum_delivery_days": method.minimum_delivery_days,
    }
    return payload


@allow_writer()
@traced_payload_generator
def _generate_excluded_shipping_methods_for_checkout_payload(
    checkout: "Checkout",
    available_shipping_methods: list[ShippingMethodData],
):
    checkout_data = json.loads(generate_checkout_payload(checkout))[0]
    payload = {
        "checkout": checkout_data,
        "shipping_methods": [
            _generate_payload_for_shipping_method(shipping_method)
            for shipping_method in available_shipping_methods
        ],
    }
    return json.dumps(payload, cls=CustomJsonEncoder)


def _get_excluded_shipping_data(
    event_type: str,
    payload_fun: Callable[[], str],
    subscribable_object: tuple["Checkout", list["ShippingMethodData"]],
    allow_replica: bool,
    requestor: Union["App", "User", None],
    pregenerated_subscription_payloads: dict | None = None,
) -> list[ExcludedShippingMethod]:
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
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    excluded_methods_map: dict[str, list[ExcludedShippingMethod]] = defaultdict(list)
    webhooks = get_webhooks_for_event(event_type)
    if webhooks:
        payload = payload_fun()

        excluded_methods_map = _get_excluded_shipping_methods_or_fetch(
            webhooks,
            event_type,
            payload,
            subscribable_object,
            allow_replica,
            requestor,
            pregenerated_subscription_payloads,
        )

    # Return a list of excluded methods, unique by id
    excluded_methods = []
    for method_id, methods in excluded_methods_map.items():
        reason = None
        if reasons := [m.reason for m in methods if m.reason]:
            reason = " ".join(reasons)
        excluded_methods.append(ExcludedShippingMethod(id=method_id, reason=reason))
    return excluded_methods


def _get_excluded_shipping_methods_or_fetch(
    webhooks: QuerySet,
    event_type: str,
    payload: str,
    subscribable_object: tuple["Checkout", list["ShippingMethodData"]],
    allow_replica: bool,
    requestor: Union["App", "User", None],
    pregenerated_subscription_payloads: dict | None = None,
) -> dict[str, list[ExcludedShippingMethod]]:
    """Return data of all excluded shipping methods.

    The data will be fetched from the cache. If missing it will fetch it from all
    defined webhooks by calling a request to each of them one by one.
    """
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    cache_data = _get_cache_data_for_exclude_shipping_methods(payload)
    excluded_methods: list[ExcludedShippingMethodSchema] = []
    # Gather responses from webhooks
    for webhook in webhooks:
        pregenerated_subscription_payload = get_pregenerated_subscription_payload(
            webhook, pregenerated_subscription_payloads
        )
        response_data = trigger_webhook_sync_if_not_cached(
            event_type=event_type,
            payload=payload,
            webhook=webhook,
            cache_data=cache_data,
            allow_replica=allow_replica,
            subscribable_object=subscribable_object,
            request_timeout=settings.WEBHOOK_SYNC_TIMEOUT,
            cache_timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            requestor=requestor,
            pregenerated_subscription_payload=pregenerated_subscription_payload,
        )
        if response_data and isinstance(response_data, dict):
            excluded_methods.extend(
                _get_excluded_shipping_methods_from_response(response_data, webhook)
            )
    return _parse_excluded_shipping_methods(excluded_methods)


def _get_cache_data_for_exclude_shipping_methods(payload: str) -> dict:
    payload_dict = json.loads(payload)
    source_object = payload_dict.get("checkout", payload_dict.get("order", {}))

    # drop fields that change between requests but are not relevant for cache key
    source_object.pop("last_change", None)
    source_object.pop("meta", None)
    source_object.pop("shipping_method", None)
    return payload_dict


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
