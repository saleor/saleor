import decimal
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import graphene
from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet

from ...payment.interface import GatewayResponse, PaymentGateway, PaymentMethodInfo
from ..base_plugin import ExcludedShippingMethod
from .const import CACHE_EXCLUDED_SHIPPING_TIME
from .tasks import _get_webhooks_for_event, send_webhook_request_sync

if TYPE_CHECKING:
    from ...app.models import App
    from ...payment.interface import PaymentData


APP_GATEWAY_ID_PREFIX = "app"

logger = logging.getLogger(__name__)


@dataclass
class PaymentAppData:
    app_pk: int
    name: str


def to_payment_app_id(app: "App", gateway_id: str) -> "str":
    return f"{APP_GATEWAY_ID_PREFIX}:{app.pk}:{gateway_id}"


def from_payment_app_id(app_gateway_id: str) -> Optional["PaymentAppData"]:
    splitted_id = app_gateway_id.split(":")
    if (
        len(splitted_id) == 3
        and splitted_id[0] == APP_GATEWAY_ID_PREFIX
        and all(splitted_id)
    ):
        try:
            app_pk = int(splitted_id[1])
        except (TypeError, ValueError):
            return None
        else:
            return PaymentAppData(app_pk, name=splitted_id[2])
    return None


def parse_list_payment_gateways_response(
    response_data: Any, app: "App"
) -> List["PaymentGateway"]:
    gateways = []
    for gateway_data in response_data:
        gateway_id = gateway_data.get("id")
        gateway_name = gateway_data.get("name")
        gateway_currencies = gateway_data.get("currencies")
        gateway_config = gateway_data.get("config")

        if gateway_id:
            gateways.append(
                PaymentGateway(
                    id=to_payment_app_id(app, gateway_id),
                    name=gateway_name,
                    currencies=gateway_currencies,
                    config=gateway_config,
                )
            )
    return gateways


def parse_payment_action_response(
    payment_information: "PaymentData",
    response_data: Any,
    transaction_kind: "str",
) -> "GatewayResponse":
    error = response_data.get("error")
    is_success = not error

    payment_method_info = None
    payment_method_data = response_data.get("payment_method")
    if payment_method_data:
        payment_method_info = PaymentMethodInfo(
            brand=payment_method_data.get("brand"),
            exp_month=payment_method_data.get("exp_month"),
            exp_year=payment_method_data.get("exp_year"),
            last_4=payment_method_data.get("last_4"),
            name=payment_method_data.get("name"),
            type=payment_method_data.get("type"),
        )

    amount = payment_information.amount
    if "amount" in response_data:
        try:
            amount = decimal.Decimal(response_data["amount"])
        except decimal.DecimalException:
            pass

    return GatewayResponse(
        action_required=response_data.get("action_required", False),
        action_required_data=response_data.get("action_required_data"),
        amount=amount,
        currency=payment_information.currency,
        customer_id=response_data.get("customer_id"),
        error=error,
        is_success=is_success,
        kind=response_data.get("kind", transaction_kind),
        payment_method_info=payment_method_info,
        raw_response=response_data,
        psp_reference=response_data.get("psp_reference"),
        transaction_id=response_data.get("transaction_id", ""),
        transaction_already_processed=response_data.get(
            "transaction_already_processed", False
        ),
    )


def get_excluded_shipping_methods_from_response(
    response_data: dict,
) -> List[dict]:
    excluded_methods = []
    for method_data in response_data.get("excluded_methods", []):
        try:
            typename, method_id = graphene.Node.from_global_id(method_data["id"])
            if typename != "ShippingMethod":
                raise ValueError(
                    f"Invalid type received. Expected ShippingMethod, got {typename}"
                )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Malformed ShippingMethod id was provided: {e}")
            continue
        excluded_methods.append(
            {"id": method_id, "reason": method_data.get("reason", "")}
        )
    return excluded_methods


def parse_excluded_shipping_methods(
    excluded_methods: List[dict],
) -> Dict[str, List[ExcludedShippingMethod]]:
    excluded_methods_map = defaultdict(list)
    for excluded_method in excluded_methods:
        method_id = excluded_method["id"]
        excluded_methods_map[method_id].append(
            ExcludedShippingMethod(
                id=method_id, reason=excluded_method.get("reason", "")
            )
        )
    return excluded_methods_map


def get_excluded_shipping_methods_or_fetch(
    webhooks: QuerySet, event_type: str, payload: str, cache_key: str
) -> Dict[str, List[ExcludedShippingMethod]]:
    """Return data of all excluded shipping methods.

    The data will be fetched from the cache. If missing it will fetch it from all
    defined webhooks by calling a request to each of them one by one.
    """
    cached_data = cache.get(cache_key)
    if cached_data:
        cached_payload, excluded_shipping_methods = cached_data
        if payload == cached_payload:
            return parse_excluded_shipping_methods(excluded_shipping_methods)

    excluded_methods = []
    # Gather responses from webhooks
    for webhook in webhooks:
        response_data = send_webhook_request_sync(
            webhook.app.name,
            webhook.target_url,
            webhook.secret_key,
            event_type,
            payload,
            timeout=settings.WEBHOOK_EXCLUDED_SHIPPING_REQUEST_TIMEOUT,
        )
        # TODO handle a case when we didn't receive a proper response
        if response_data:
            excluded_methods.extend(
                get_excluded_shipping_methods_from_response(response_data)
            )
    cache.set(cache_key, (payload, excluded_methods), CACHE_EXCLUDED_SHIPPING_TIME)
    return parse_excluded_shipping_methods(excluded_methods)


def get_excluded_shipping_data(
    event_type: str,
    previous_value: List[ExcludedShippingMethod],
    payload_fun: Callable[[], str],
    cache_key: str,
) -> List[ExcludedShippingMethod]:
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

    excluded_methods_map: Dict[str, List[ExcludedShippingMethod]] = defaultdict(list)
    webhooks = _get_webhooks_for_event(event_type)
    if webhooks:
        payload = payload_fun()

        excluded_methods_map = get_excluded_shipping_methods_or_fetch(
            webhooks, event_type, payload, cache_key
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
