import base64
import json
import logging
from collections import defaultdict
from typing import Any, Callable, Optional, Union

from django.db.models import QuerySet
from graphql import GraphQLError
from prices import Money

from ...app.models import App
from ...checkout.models import Checkout
from ...graphql.core.utils import from_global_id_or_error
from ...graphql.shipping.types import ShippingMethod
from ...order.models import Order
from ...plugins.base_plugin import ExcludedShippingMethod, RequestorOrLazyObject
from ...settings import WEBHOOK_SYNC_TIMEOUT
from ...shipping.interface import ShippingMethodData
from ...webhook.utils import get_webhooks_for_event
from ..const import APP_ID_PREFIX, CACHE_EXCLUDED_SHIPPING_TIME
from .synchronous.transport import trigger_webhook_sync_if_not_cached

logger = logging.getLogger(__name__)


def to_shipping_app_id(app: App, shipping_method_id: str) -> str:
    app_identifier = app.identifier or app.id
    return base64.b64encode(
        str.encode(f"{APP_ID_PREFIX}:{app_identifier}:{shipping_method_id}")
    ).decode("utf-8")


def convert_to_app_id_with_identifier(shipping_app_id: str) -> None | str:
    """Prepare the shipping_app_id in format `app:<app-identifier>/method_id>`.

    The format of shipping_app_id has been changes so we need to support both of them.
    This method is preparing the new shipping_app_id format based on assumptions
    that right now the old one is used which is `app:<app-pk>:method_id>`
    """
    decoded_id = base64.b64decode(shipping_app_id).decode()
    splitted_id = decoded_id.split(":")
    if len(splitted_id) != 3:
        return None
    try:
        app_id = int(splitted_id[1])
    except (TypeError, ValueError):
        return None
    app = App.objects.filter(id=app_id).first()
    if app is None:
        return None
    return to_shipping_app_id(app, splitted_id[2])


def method_metadata_is_valid(metadata) -> bool:
    if not isinstance(metadata, dict):
        return False
    for key, value in metadata.items():
        if not isinstance(key, str) or not isinstance(value, str) or not key.strip():
            return False
    return True


def parse_list_shipping_methods_response(
    response_data: Any, app: "App"
) -> list["ShippingMethodData"]:
    shipping_methods = []
    for shipping_method_data in response_data:
        if not validate_shipping_method_data(shipping_method_data):
            continue
        method_id = shipping_method_data.get("id")
        method_name = shipping_method_data.get("name")
        method_amount = shipping_method_data.get("amount")
        method_currency = shipping_method_data.get("currency")
        method_maximum_delivery_days = shipping_method_data.get("maximum_delivery_days")
        method_minimum_delivery_days = shipping_method_data.get("minimum_delivery_days")
        method_description = shipping_method_data.get("description")
        method_metadata = shipping_method_data.get("metadata") or {}
        if method_metadata:
            method_metadata = (
                method_metadata if method_metadata_is_valid(method_metadata) else {}
            )

        shipping_methods.append(
            ShippingMethodData(
                id=to_shipping_app_id(app, method_id),
                name=method_name,
                price=Money(method_amount, method_currency),
                maximum_delivery_days=method_maximum_delivery_days,
                minimum_delivery_days=method_minimum_delivery_days,
                description=method_description,
                metadata=method_metadata,
            )
        )
    return shipping_methods


def validate_shipping_method_data(shipping_method_data):
    if not isinstance(shipping_method_data, dict):
        return False
    keys = ["id", "name", "amount", "currency"]
    return all(key in shipping_method_data for key in keys)


def get_cache_data_for_exclude_shipping_methods(payload: str) -> dict:
    payload_dict = json.loads(payload)
    source_object = payload_dict.get("checkout", payload_dict.get("order", {}))

    # drop fields that change between requests but are not relevant for cache key
    source_object.pop("last_change", None)
    source_object.pop("meta", None)
    source_object.pop("shipping_method", None)
    return payload_dict


def get_excluded_shipping_methods_or_fetch(
    webhooks: QuerySet,
    event_type: str,
    payload: str,
    subscribable_object: Optional[Union["Order", "Checkout"]],
    allow_replica: bool,
    requestor: Optional[RequestorOrLazyObject],
) -> dict[str, list[ExcludedShippingMethod]]:
    """Return data of all excluded shipping methods.

    The data will be fetched from the cache. If missing it will fetch it from all
    defined webhooks by calling a request to each of them one by one.
    """
    cache_data = get_cache_data_for_exclude_shipping_methods(payload)
    excluded_methods = []
    # Gather responses from webhooks
    for webhook in webhooks:
        response_data = trigger_webhook_sync_if_not_cached(
            event_type=event_type,
            payload=payload,
            webhook=webhook,
            cache_data=cache_data,
            allow_replica=allow_replica,
            subscribable_object=subscribable_object,
            request_timeout=WEBHOOK_SYNC_TIMEOUT,
            cache_timeout=CACHE_EXCLUDED_SHIPPING_TIME,
            requestor=requestor,
        )
        if response_data and isinstance(response_data, dict):
            excluded_methods.extend(
                get_excluded_shipping_methods_from_response(response_data)
            )
    return parse_excluded_shipping_methods(excluded_methods)


def get_excluded_shipping_data(
    event_type: str,
    previous_value: list[ExcludedShippingMethod],
    payload_fun: Callable[[], str],
    subscribable_object: Optional[Union["Order", "Checkout"]],
    allow_replica: bool,
    requestor: Optional[RequestorOrLazyObject] = None,
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

    excluded_methods_map: dict[str, list[ExcludedShippingMethod]] = defaultdict(list)
    webhooks = get_webhooks_for_event(event_type)
    if webhooks:
        payload = payload_fun()

        excluded_methods_map = get_excluded_shipping_methods_or_fetch(
            webhooks, event_type, payload, subscribable_object, allow_replica, requestor
        )

    # Gather responses for previous plugins
    for method in previous_value:
        excluded_methods_map[method.id].append(method)

    # Return a list of excluded methods, unique by id
    excluded_methods = []
    for method_id, methods in excluded_methods_map.items():
        reason = None
        if reasons := [m.reason for m in methods if m.reason]:
            reason = " ".join(reasons)
        excluded_methods.append(ExcludedShippingMethod(id=method_id, reason=reason))
    return excluded_methods


def get_excluded_shipping_methods_from_response(
    response_data: dict,
) -> list[dict]:
    excluded_methods = []
    for method_data in response_data.get("excluded_methods", []):
        try:
            type_name, method_id = from_global_id_or_error(method_data["id"])
            if type_name not in (APP_ID_PREFIX, str(ShippingMethod)):
                logger.warning(
                    "Invalid type received. Expected ShippingMethod, got %s", type_name
                )
                continue

        except (KeyError, ValueError, TypeError, GraphQLError) as e:
            logger.warning("Malformed ShippingMethod id was provided: %s", e)
            continue
        excluded_methods.append(
            {"id": method_id, "reason": method_data.get("reason", "")}
        )
    return excluded_methods


def parse_excluded_shipping_methods(
    excluded_methods: list[dict],
) -> dict[str, list[ExcludedShippingMethod]]:
    excluded_methods_map = defaultdict(list)
    for excluded_method in excluded_methods:
        method_id = excluded_method["id"]
        excluded_methods_map[method_id].append(
            ExcludedShippingMethod(
                id=method_id, reason=excluded_method.get("reason", "")
            )
        )
    return excluded_methods_map


def get_cache_data_for_shipping_list_methods_for_checkout(payload: str) -> dict:
    key_data = json.loads(payload)

    # drop fields that change between requests but are not relevant for cache key
    key_data[0].pop("last_change")
    key_data[0].pop("meta")
    # Drop the external_app_shipping_id from the cache key as it should not have an
    # impact on cache invalidation
    if "external_app_shipping_id" in key_data[0].get("private_metadata", {}):
        del key_data[0]["private_metadata"]["external_app_shipping_id"]
    return key_data
