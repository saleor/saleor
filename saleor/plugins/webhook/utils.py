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
from ...payment import TokenizedPaymentFlow
from ...payment.interface import (
    GatewayResponse,
    PaymentGateway,
    PaymentMethodCreditCardInfo,
    PaymentMethodData,
    PaymentMethodInfo,
)
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
    splitted_id = app_gateway_id.split(":")
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


def get_delivery_for_webhook(event_delivery_id) -> Optional["EventDelivery"]:
    try:
        delivery = EventDelivery.objects.select_related("payload", "webhook__app").get(
            id=event_delivery_id
        )
    except EventDelivery.DoesNotExist:
        logger.error("Event delivery id: %r not found", event_delivery_id)
        return None

    if not delivery.webhook.is_active:
        delivery_update(delivery=delivery, status=EventDeliveryStatus.FAILED)
        logger.info("Event delivery id: %r webhook is disabled.", event_delivery_id)
        return None
    return delivery


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
        App.objects.order_by("pk")
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


def get_credit_card_info(
    app: App, credit_card_info: dict
) -> Optional[PaymentMethodCreditCardInfo]:
    required_fields = [
        "brand",
        "lastDigits",
        "expYear",
        "expMonth",
    ]
    brand = credit_card_info.get("brand")
    last_digits = credit_card_info.get("lastDigits")
    exp_year = credit_card_info.get("expYear")
    exp_month = credit_card_info.get("expMonth")
    first_digits = credit_card_info.get("firstDigits")
    if not all(field in credit_card_info for field in required_fields):
        logger.warning(
            "Skipping stored payment method. Missing required fields for credit card "
            "info. Required fields: %s, received fields: %s from app %s.",
            required_fields,
            credit_card_info.keys(),
            app.id,
        )
        return None
    if not all([brand, last_digits, exp_year, exp_month]):
        logger.warning("Skipping stored credit card info without required fields")
        return None
    if not isinstance(exp_year, int):
        if isinstance(exp_year, str) and exp_year.isdigit():
            exp_year = int(exp_year)
        else:
            logger.warning(
                "Skipping stored payment method with invalid expYear, "
                "received from app %s",
                app.id,
            )
            return None

    if not isinstance(exp_month, int):
        if isinstance(exp_month, str) and exp_month.isdigit():
            exp_month = int(exp_month)
        else:
            logger.warning(
                "Skipping stored payment method with invalid expMonth, "
                "received from app %s",
                app.id,
            )
            return None

    return PaymentMethodCreditCardInfo(
        brand=str(brand),
        last_digits=str(last_digits),
        exp_year=exp_year,
        exp_month=exp_month,
        first_digits=str(first_digits) if first_digits else None,
    )


def get_payment_method_from_response(
    app: "App", payment_method: dict
) -> Optional[PaymentMethodData]:
    payment_method_external_id = payment_method.get("id")
    if not payment_method_external_id:
        logger.warning(
            "Skipping stored payment method without id, received from app %s", app.id
        )
        return None
    payment_method_type = payment_method.get("type")
    if not payment_method_type:
        logger.warning(
            "Skipping stored payment method without type, received from app %s",
            app.id,
        )
        return None

    supported_payment_flows = payment_method.get("supportedPaymentFlows")
    if not supported_payment_flows or not isinstance(supported_payment_flows, list):
        logger.warning(
            "Skipping stored payment method with incorrect `supportedPaymentFlows`, "
            "received from app %s",
            app.id,
        )
        return None
    payment_flow_choices = [flow[0].upper() for flow in TokenizedPaymentFlow.CHOICES]
    if set(supported_payment_flows).difference(payment_flow_choices):
        logger.warning(
            "Skipping stored payment method with unsupported payment flows, "
            "received from app %s",
            app.id,
        )
        return None

    credit_card_info = payment_method.get("creditCardInfo")
    name = payment_method.get("name")
    return PaymentMethodData(
        id=to_payment_app_id(app, payment_method_external_id),
        external_id=payment_method_external_id,
        supported_payment_flows=supported_payment_flows,
        type=payment_method_type,
        credit_card_info=get_credit_card_info(app, credit_card_info)
        if credit_card_info
        else None,
        name=name if name else None,
        data=payment_method.get("data"),
        gateway=app,
    )


def get_list_stored_payment_methods_from_response(
    app: "App", response_data: dict
) -> list["PaymentMethodData"]:
    payment_methods_response = response_data.get("paymentMethods", [])
    payment_methods = []
    for payment_method in payment_methods_response:
        if parsed_payment_method := get_payment_method_from_response(
            app, payment_method
        ):
            payment_methods.append(parsed_payment_method)
    return payment_methods
