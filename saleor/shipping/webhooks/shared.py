import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Union

from django.conf import settings
from django.db.models import QuerySet
from promise import Promise
from pydantic import ValidationError

from ...webhook.models import Webhook
from ...webhook.response_schemas.shipping import (
    ExcludedShippingMethodSchema,
    FilterShippingMethodsSchema,
)
from ...webhook.transport.synchronous.transport import (
    trigger_webhook_sync_promise,
    trigger_webhook_sync_promise_if_not_cached,
)
from ..interface import ExcludedShippingMethod, ShippingMethodData

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App
    from ...checkout.models import Checkout
    from ...order.models import Order

CACHE_EXCLUDED_SHIPPING_TIME = 60 * 3

logger = logging.getLogger(__name__)


def generate_payload_for_shipping_method(method: ShippingMethodData):
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


def _get_excluded_shipping_methods_or_fetch(
    webhooks: QuerySet,
    event_type: str,
    static_payload: str,
    subscribable_object: "tuple[Order | Checkout, list[ShippingMethodData]]",
    allow_replica: bool,
    requestor: Union["App", "User", None],
    cache_data: dict | None,
) -> Promise[dict[str, list[ExcludedShippingMethod]]]:
    """Return data of all excluded shipping methods.

    The data will be fetched from the cache if present and cache_data was provided.
    If missing it will fetch it from all defined webhooks by calling a request to
    each of them one by one.
    """
    promised_responses = []
    for webhook in webhooks:
        # The approach for Order and Checkout is the same, except that
        # Checkout does not need a cache anymore as all deliveries and their
        # data are denormalized. The same flow will be introduced for the Order
        # but for now we use cache_data as a indicator to decide if we want to
        # use the cache approach. This will be fully dropped after introducing
        # denormalized deliveries for Order.
        if cache_data is not None:
            response_promise = trigger_webhook_sync_promise_if_not_cached(
                event_type=event_type,
                static_payload=static_payload,
                webhook=webhook,
                cache_data=cache_data,
                allow_replica=allow_replica,
                subscribable_object=subscribable_object,
                request_timeout=settings.WEBHOOK_SYNC_TIMEOUT,
                cache_timeout=CACHE_EXCLUDED_SHIPPING_TIME,
                requestor=requestor,
            )
        else:
            response_promise = trigger_webhook_sync_promise(
                event_type=event_type,
                static_payload=static_payload,
                webhook=webhook,
                allow_replica=allow_replica,
                subscribable_object=subscribable_object,
                requestor=requestor,
                timeout=settings.WEBHOOK_SYNC_TIMEOUT,
            )
        promised_responses.append(response_promise)

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


def get_excluded_shipping_data(
    webhooks: QuerySet[Webhook],
    event_type: str,
    static_payload: str,
    subscribable_object: "tuple[Order | Checkout, list[ShippingMethodData]]",
    allow_replica: bool,
    requestor: Union["App", "User", None],
    cache_data: dict | None,
) -> Promise[list[ExcludedShippingMethod]]:
    """Exclude not allowed shipping methods by sync webhook.

    Fetch excluded shipping methods from sync webhooks and return them as a list of
    excluded shipping methods.
    When cache_data is provided, the function uses it to built cache and reduce the number of
    requests which we call to the external APIs. In case when we have the same payload
    in a cache as we're going to send now, we will skip an additional request and use
    the response fetched from cache.
    The function will fetch the payload only in the case that we have any defined
    webhook.
    """

    def merge_excluded_methods_map(
        excluded_methods_map: dict[str, list[ExcludedShippingMethod]],
    ) -> list[ExcludedShippingMethod]:
        excluded_methods = []
        for method_id, methods in excluded_methods_map.items():
            reason = None
            if reasons := [m.reason for m in methods if m.reason]:
                reason = " ".join(reasons)
            excluded_methods.append(ExcludedShippingMethod(id=method_id, reason=reason))
        return excluded_methods

    return _get_excluded_shipping_methods_or_fetch(
        webhooks,
        event_type,
        static_payload,
        subscribable_object,
        allow_replica,
        requestor,
        cache_data=cache_data,
    ).then(merge_excluded_methods_map)
