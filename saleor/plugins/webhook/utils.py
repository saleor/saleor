import base64
import decimal
import json
from contextlib import contextmanager
from dataclasses import dataclass
from time import time
from typing import TYPE_CHECKING, Any, List, Optional

from django.db.models import QuerySet
from prices import Money

from ...core.models import (
    EventDelivery,
    EventDeliveryAttempt,
    EventDeliveryStatus,
    EventPayload,
)
from ...payment.interface import GatewayResponse, PaymentGateway, PaymentMethodInfo
from ...shipping.interface import ShippingMethodData

if TYPE_CHECKING:
    from ...app.models import App
    from ...payment.interface import PaymentData
    from .tasks import WebhookResponse


APP_ID_PREFIX = "app"


@dataclass
class PaymentAppData:
    app_pk: int
    name: str


@dataclass
class ShippingAppData:
    app_pk: int
    shipping_method_id: str


def to_payment_app_id(app: "App", gateway_id: str) -> "str":
    return f"{APP_ID_PREFIX}:{app.pk}:{gateway_id}"


def to_shipping_app_id(app: "App", shipping_method_id: str) -> "str":
    return base64.b64encode(
        str.encode(f"{APP_ID_PREFIX}:{app.pk}:{shipping_method_id}")
    ).decode("utf-8")


def from_payment_app_id(app_gateway_id: str) -> Optional["PaymentAppData"]:
    splitted_id = app_gateway_id.split(":")
    if len(splitted_id) == 3 and splitted_id[0] == APP_ID_PREFIX and all(splitted_id):
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


def parse_list_shipping_methods_response(
    response_data: Any, app: "App"
) -> List["ShippingMethodData"]:
    shipping_methods = []
    for shipping_method_data in response_data:
        method_id = shipping_method_data.get("id")
        method_name = shipping_method_data.get("name")
        method_amount = shipping_method_data.get("amount")
        method_currency = shipping_method_data.get("currency")
        method_maximum_delivery_days = shipping_method_data.get("maximum_delivery_days")

        shipping_methods.append(
            ShippingMethodData(
                id=to_shipping_app_id(app, method_id),
                name=method_name,
                price=Money(method_amount, method_currency),
                maximum_delivery_days=method_maximum_delivery_days,
            )
        )
    return shipping_methods


@contextmanager
def catch_duration_time():
    start = time()
    yield lambda: time() - start


def create_event_delivery_list_for_webhooks(
    webhooks: QuerySet,
    event_payload: "EventPayload",
    event_type: str,
) -> List[EventDelivery]:

    event_deliveries = EventDelivery.objects.bulk_create(
        [
            EventDelivery(
                status=EventDeliveryStatus.PENDING,
                event_type=event_type,
                payload=event_payload,
                webhook=webhook,
            )
            for webhook in webhooks
        ]
    )
    return event_deliveries


def create_attempt(
    delivery: "EventDelivery",
    task_id: str = None,
):
    attempt = EventDeliveryAttempt.objects.create(
        delivery=delivery,
        task_id=task_id,
        duration=None,
        response=None,
        request_headers=None,
        response_headers=None,
        status=EventDeliveryStatus.PENDING,
    )
    return attempt


def attempt_update(
    attempt: "EventDeliveryAttempt",
    webhook_response: "WebhookResponse",
):

    attempt.duration = webhook_response.duration
    attempt.response = webhook_response.content
    attempt.response_headers = json.dumps(webhook_response.response_headers)
    attempt.request_headers = json.dumps(webhook_response.request_headers)
    attempt.status = webhook_response.status
    attempt.save(
        update_fields=[
            "duration",
            "response",
            "response_headers",
            "request_headers",
            "status",
        ]
    )


def delivery_update(delivery: "EventDelivery", status: str):
    delivery.status = status
    delivery.save(update_fields=["status"])


def clear_successful_delivery(delivery: "EventDelivery"):
    if delivery.status == EventDeliveryStatus.SUCCESS:
        delivery.delete()
