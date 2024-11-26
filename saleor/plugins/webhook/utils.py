import decimal
import hashlib
import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from time import time
from typing import TYPE_CHECKING, Any, List, Optional, Sequence

from ...app.models import App
from ...core.models import (
    EventDelivery,
    EventDeliveryAttempt,
    EventDeliveryStatus,
    EventPayload,
)
from ...core.taxes import TaxData, TaxLineData
from ...payment.interface import GatewayResponse, PaymentGateway, PaymentMethodInfo
from ...webhook.event_types import WebhookEventSyncType
from ..const import APP_ID_PREFIX

if TYPE_CHECKING:
    from ...payment.interface import PaymentData
    from ...webhook.models import Webhook
    from .tasks import WebhookResponse


logger = logging.getLogger(__name__)


@dataclass
class PaymentAppData:
    app_pk: Optional[int]
    app_identifier: Optional[str]
    name: str


def to_payment_app_id(app: "App", external_id: str) -> "str":
    app_identifier = app.identifier or app.id
    return f"{APP_ID_PREFIX}:{app_identifier}:{external_id}"


def from_payment_app_id(app_gateway_id: str) -> Optional["PaymentAppData"]:
    splitted_id = app_gateway_id.split(":", maxsplit=2)
    if len(splitted_id) == 3 and splitted_id[0] == APP_ID_PREFIX and all(splitted_id):
        try:
            app_pk = int(splitted_id[1])
        except (TypeError, ValueError):
            return PaymentAppData(
                app_identifier=splitted_id[1], app_pk=None, name=splitted_id[2]
            )
        else:
            return PaymentAppData(
                app_pk=app_pk, app_identifier=None, name=splitted_id[2]
            )
    return None


def parse_list_payment_gateways_response(
    response_data: Any, app: "App"
) -> List["PaymentGateway"]:
    gateways: List[PaymentGateway] = []
    if not isinstance(response_data, list):
        return gateways

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


def _unsafe_parse_tax_line_data(
    tax_line_data_response: Any,
) -> TaxLineData:
    """Unsafe TaxLineData parser.

    Raises KeyError or DecimalException on invalid data.
    """
    total_gross_amount = decimal.Decimal(tax_line_data_response["total_gross_amount"])
    total_net_amount = decimal.Decimal(tax_line_data_response["total_net_amount"])
    tax_rate = decimal.Decimal(tax_line_data_response["tax_rate"])

    return TaxLineData(
        total_gross_amount=total_gross_amount,
        total_net_amount=total_net_amount,
        tax_rate=tax_rate,
    )


def _unsafe_parse_tax_data(
    tax_data_response: Any,
) -> TaxData:
    """Unsafe TaxData parser.

    Raises KeyError or DecimalException on invalid data.
    """
    shipping_price_gross_amount = decimal.Decimal(
        tax_data_response["shipping_price_gross_amount"]
    )
    shipping_price_net_amount = decimal.Decimal(
        tax_data_response["shipping_price_net_amount"]
    )
    shipping_tax_rate = decimal.Decimal(tax_data_response["shipping_tax_rate"])
    lines = [_unsafe_parse_tax_line_data(line) for line in tax_data_response["lines"]]

    return TaxData(
        shipping_price_gross_amount=shipping_price_gross_amount,
        shipping_price_net_amount=shipping_price_net_amount,
        shipping_tax_rate=shipping_tax_rate,
        lines=lines,
    )


def parse_tax_data(
    response_data: Any,
) -> Optional[TaxData]:
    try:
        return _unsafe_parse_tax_data(response_data)
    except (TypeError, KeyError, decimal.DecimalException):
        return None


def get_delivery_for_webhook(
    event_delivery_id,
) -> tuple[Optional["EventDelivery"], bool]:
    not_found = False
    try:
        delivery = EventDelivery.objects.select_related("payload", "webhook__app").get(
            id=event_delivery_id
        )
    except EventDelivery.DoesNotExist:
        not_found = True
        logger.error("Event delivery id: %r not found", event_delivery_id)
        return None, not_found

    if not delivery.webhook.is_active:
        delivery_update(delivery=delivery, status=EventDeliveryStatus.FAILED)
        logger.info("Event delivery id: %r webhook is disabled.", event_delivery_id)
        return None, not_found
    return delivery, not_found


@contextmanager
def catch_duration_time():
    start = time()
    yield lambda: time() - start


def create_event_delivery_list_for_webhooks(
    webhooks: Sequence["Webhook"],
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
    task_id: Optional[str] = None,
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
    attempt.response_status_code = webhook_response.response_status_code
    attempt.request_headers = json.dumps(webhook_response.request_headers)
    attempt.status = webhook_response.status
    attempt.save(
        update_fields=[
            "duration",
            "response",
            "response_headers",
            "response_status_code",
            "request_headers",
            "status",
        ]
    )


def delivery_update(delivery: "EventDelivery", status: str):
    delivery.status = status
    delivery.save(update_fields=["status"])


def clear_successful_delivery(delivery: "EventDelivery"):
    if delivery.status == EventDeliveryStatus.SUCCESS:
        payload_id = delivery.payload_id
        delivery.delete()
        if payload_id:
            EventPayload.objects.filter(pk=payload_id, deliveries__isnull=True).delete()


DEFAULT_TAX_CODE = "UNMAPPED"
DEFAULT_TAX_DESCRIPTION = "Unmapped Product/Product Type"


def get_current_tax_app() -> Optional[App]:
    """Return currently used tax app or None, if there aren't any."""
    return (
        App.objects.filter(removed_at__isnull=True)
        .order_by("pk")
        .for_event_type(WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES)
        .for_event_type(WebhookEventSyncType.ORDER_CALCULATE_TAXES)
        .last()
    )


def get_meta_code_key(app: App) -> str:
    return f"{app.identifier}.code"


def get_meta_description_key(app: App) -> str:
    return f"{app.identifier}.description"


def generate_cache_key_for_webhook(
    key_data: dict, webhook_url: str, event: str, app_id: int
) -> str:
    """Generate cache key for webhook.

    Cache key takes into account the webhook url, event type, and app id.
    The response from webhook_url can be different for different events.
    Apps can have assigned different permissions, so the response can vary for
    different apps.
    """
    key = json.dumps(key_data)
    return (
        f"{app_id}-{webhook_url}-{event}-"
        f"{hashlib.sha256(key.encode('utf-8')).hexdigest()}"
    )
