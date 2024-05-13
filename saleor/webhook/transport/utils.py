import decimal
import hashlib
import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from time import time
from typing import Any, Callable, Optional
from urllib.parse import unquote, urlparse, urlunparse

import boto3
from botocore.exceptions import ClientError
from celery import Task
from celery.exceptions import MaxRetriesExceededError, Retry
from celery.utils.log import get_task_logger
from django.conf import settings
from django.urls import reverse
from google.cloud import pubsub_v1
from requests import RequestException
from requests_hardened.ip_filter import InvalidIPAddress

from ...app.headers import AppHeaders, DeprecatedAppHeaders
from ...app.models import App
from ...core.db.connection import allow_writer
from ...core.http_client import HTTPClient
from ...core.models import (
    EventDelivery,
    EventDeliveryAttempt,
    EventDeliveryStatus,
    EventPayload,
)
from ...core.taxes import TaxData, TaxLineData
from ...core.utils import build_absolute_uri
from ...core.utils.events import call_event
from ...payment import PaymentError
from ...payment.interface import (
    GatewayResponse,
    PaymentData,
    PaymentGateway,
    PaymentMethodInfo,
    TransactionActionData,
)
from ...payment.utils import (
    create_failed_transaction_event,
    recalculate_refundable_for_checkout,
)
from ...webhook.utils import get_webhooks_for_event
from .. import observability
from ..const import APP_ID_PREFIX
from ..event_types import WebhookEventSyncType
from ..models import Webhook
from . import signature_for_payload

logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)


DEFAULT_TAX_CODE = "UNMAPPED"
DEFAULT_TAX_DESCRIPTION = "Unmapped Product/Product Type"


class WebhookSchemes(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    AWS_SQS = "awssqs"
    GOOGLE_CLOUD_PUBSUB = "gcpubsub"


@dataclass
class PaymentAppData:
    app_pk: Optional[int]
    app_identifier: Optional[str]
    name: str


@dataclass
class WebhookResponse:
    content: str
    request_headers: Optional[dict] = None
    response_headers: Optional[dict] = None
    response_status_code: Optional[int] = None
    status: str = EventDeliveryStatus.SUCCESS
    duration: float = 0.0


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


def send_webhook_using_http(
    target_url,
    message,
    domain,
    signature,
    event_type,
    timeout=settings.WEBHOOK_TIMEOUT,
    custom_headers: Optional[dict[str, str]] = None,
) -> WebhookResponse:
    """Send a webhook request using http / https protocol.

    :param target_url: Target URL request will be sent to.
    :param message: Payload that will be used.
    :param domain: Current site domain.
    :param signature: Webhook secret key checksum.
    :param event_type: Webhook event type.
    :param timeout: Request timeout.
    :param custom_headers: Custom headers which will be added to request headers.

    :return: WebhookResponse object.
    """
    headers = {
        "Content-Type": "application/json",
        # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
        DeprecatedAppHeaders.EVENT_TYPE: event_type,
        DeprecatedAppHeaders.DOMAIN: domain,
        DeprecatedAppHeaders.SIGNATURE: signature,
        AppHeaders.EVENT_TYPE: event_type,
        AppHeaders.DOMAIN: domain,
        AppHeaders.SIGNATURE: signature,
        AppHeaders.API_URL: build_absolute_uri(reverse("api"), domain),
    }

    if custom_headers:
        headers.update(custom_headers)

    try:
        response = HTTPClient.send_request(
            "POST",
            target_url,
            data=message,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
        )
    except RequestException as e:
        if e.response:
            return WebhookResponse(
                content=e.response.text,
                status=EventDeliveryStatus.FAILED,
                request_headers=headers,
                response_headers=dict(e.response.headers),
                response_status_code=e.response.status_code,
            )

        if isinstance(e, InvalidIPAddress):
            message = "Invalid IP address"
        else:
            message = str(e)
        result = WebhookResponse(
            content=message,
            status=EventDeliveryStatus.FAILED,
            request_headers=headers,
        )
        return result

    return WebhookResponse(
        content=response.text,
        request_headers=headers,
        response_headers=dict(response.headers),
        response_status_code=response.status_code,
        duration=response.elapsed.total_seconds(),
        status=(
            EventDeliveryStatus.SUCCESS
            if 200 <= response.status_code < 300
            else EventDeliveryStatus.FAILED
        ),
    )


def send_webhook_using_aws_sqs(
    target_url, message, domain, signature, event_type, **kwargs
) -> WebhookResponse:
    parts = urlparse(target_url)
    region = "us-east-1"
    hostname_parts = parts.hostname.split(".")
    if len(hostname_parts) == 4 and hostname_parts[0] == "sqs":
        region = hostname_parts[1]
    client = boto3.client(
        "sqs",
        region_name=region,
        aws_access_key_id=parts.username,
        aws_secret_access_key=(
            unquote(parts.password) if parts.password else parts.password
        ),
    )
    queue_url = urlunparse(
        (
            "https",
            parts.hostname,
            parts.path,
            parts.params,
            parts.query,
            parts.fragment,
        )
    )
    is_fifo = parts.path.endswith(".fifo")

    msg_attributes = {
        "SaleorDomain": {"DataType": "String", "StringValue": domain},
        "SaleorApiUrl": {
            "DataType": "String",
            "StringValue": build_absolute_uri(reverse("api"), domain),
        },
        "EventType": {"DataType": "String", "StringValue": event_type},
    }
    if signature:
        msg_attributes["Signature"] = {
            "DataType": "String",
            "StringValue": signature,
        }

    message_kwargs = {
        "QueueUrl": queue_url,
        "MessageAttributes": msg_attributes,
        "MessageBody": message.decode("utf-8"),
    }
    if is_fifo:
        message_kwargs["MessageGroupId"] = domain
    with catch_duration_time() as duration:
        try:
            response = json.dumps(client.send_message(**message_kwargs))
        except (ClientError,) as e:
            return WebhookResponse(
                content=str(e), status=EventDeliveryStatus.FAILED, duration=duration()
            )
        return WebhookResponse(content=response, duration=duration())


def send_webhook_using_google_cloud_pubsub(
    target_url, message, domain, signature, event_type, **kwargs
):
    parts = urlparse(target_url)
    client = pubsub_v1.PublisherClient()
    topic_name = parts.path[1:]  # drop the leading slash
    with catch_duration_time() as duration:
        try:
            future = client.publish(
                topic_name,
                message,
                saleorDomain=domain,
                saleorApiUrl=build_absolute_uri(reverse("api"), domain),
                eventType=event_type,
                signature=signature,
            )
        except (pubsub_v1.publisher.exceptions.MessageTooLargeError, RuntimeError) as e:
            return WebhookResponse(content=str(e), status=EventDeliveryStatus.FAILED)
        response_duration = duration()
        response = future.result()
        return WebhookResponse(content=response, duration=response_duration)


def send_webhook_using_scheme_method(
    target_url,
    domain,
    secret,
    event_type,
    data,
    custom_headers=None,
) -> WebhookResponse:
    parts = urlparse(target_url)
    message = data if isinstance(data, bytes) else data.encode("utf-8")
    signature = signature_for_payload(message, secret)
    scheme_matrix: dict[WebhookSchemes, Callable] = {
        WebhookSchemes.HTTP: send_webhook_using_http,
        WebhookSchemes.HTTPS: send_webhook_using_http,
        WebhookSchemes.AWS_SQS: send_webhook_using_aws_sqs,
        WebhookSchemes.GOOGLE_CLOUD_PUBSUB: send_webhook_using_google_cloud_pubsub,
    }

    if send_method := scheme_matrix.get(parts.scheme.lower()):
        # try:
        return send_method(
            target_url,
            message,
            domain,
            signature,
            event_type,
            custom_headers=custom_headers,
        )
    raise ValueError(f"Unknown webhook scheme: {parts.scheme!r}")


def handle_webhook_retry(
    celery_task: Task,
    webhook: Webhook,
    response: WebhookResponse,
    delivery: EventDelivery,
    delivery_attempt: EventDeliveryAttempt,
) -> bool:
    """Handle celery retry for webhook requests.

    Calls retry to re-run the celery_task by raising Retry exception.
    When MaxRetriesExceededError is raised the function will end without exception.
    """
    is_success = True
    log_extra_details = {
        "webhook": {
            "id": webhook.id,
            "target_url": webhook.target_url,
            "event": delivery.event_type,
            "execution_mode": "async",
            "duration": response.duration,
            "http_status_code": response.response_status_code,
        },
    }
    task_logger.info(
        "[Webhook ID: %r] Failed request to %r: %r for event: %r."
        " Delivery attempt id: %r",
        webhook.id,
        webhook.target_url,
        response.content,
        delivery.event_type,
        delivery_attempt.id,
        extra=log_extra_details,
    )
    if response.response_status_code and 300 <= response.response_status_code < 500:
        # do not retry for 30x and 40x status codes
        task_logger.info(
            "[Webhook ID: %r] Failed request to %r: received HTTP %d. Delivery ID: %r",
            webhook.id,
            webhook.target_url,
            response.response_status_code,
            delivery.id,
            extra=log_extra_details,
        )
        return False
    try:
        countdown = celery_task.retry_backoff * (2**celery_task.request.retries)
        celery_task.retry(countdown=countdown, **celery_task.retry_kwargs)
    except Retry as retry_error:
        next_retry = observability.task_next_retry_date(retry_error)
        observability.report_event_delivery_attempt(delivery_attempt, next_retry)
        raise retry_error
    except MaxRetriesExceededError:
        is_success = False
        task_logger.info(
            "[Webhook ID: %r] Failed request to %r: exceeded retry limit. Delivery ID: %r",
            webhook.id,
            webhook.target_url,
            delivery.id,
            extra=log_extra_details,
        )
    return is_success


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


@allow_writer()
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


@allow_writer()
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


@allow_writer()
def clear_successful_delivery(delivery: "EventDelivery"):
    if delivery.status == EventDeliveryStatus.SUCCESS:
        payload_id = delivery.payload_id
        delivery.delete()
        if payload_id:
            EventPayload.objects.filter(pk=payload_id, deliveries__isnull=True).delete()


@allow_writer()
def delivery_update(delivery: "EventDelivery", status: str):
    delivery.status = status
    delivery.save(update_fields=["status"])


def trigger_transaction_request(
    transaction_data: "TransactionActionData", event_type: str, requestor
):
    from ..payloads import generate_transaction_action_request_payload
    from .synchronous.transport import (
        create_delivery_for_subscription_sync_event,
        handle_transaction_request_task,
    )

    if not transaction_data.transaction_app_owner:
        create_failed_transaction_event(
            transaction_data.event,
            cause=(
                "Cannot process the action as the given transaction is not "
                "attached to any app."
            ),
        )
        recalculate_refundable_for_checkout(
            transaction_data.transaction, transaction_data.event
        )
        return None
    webhook = get_webhooks_for_event(
        event_type, apps_ids=[transaction_data.transaction_app_owner.pk]
    ).first()
    if not webhook:
        create_failed_transaction_event(
            transaction_data.event,
            cause="Cannot find a webhook that can process the action.",
        )
        recalculate_refundable_for_checkout(
            transaction_data.transaction, transaction_data.event
        )
        return None

    if webhook.subscription_query:
        delivery = None
        try:
            delivery = create_delivery_for_subscription_sync_event(
                event_type=event_type,
                subscribable_object=transaction_data,
                webhook=webhook,
            )
        except PaymentError as e:
            logger.warning("Failed to create delivery for subscription webhook: %s", e)
        if not delivery:
            create_failed_transaction_event(
                transaction_data.event,
                cause="Cannot generate a payload for the action.",
            )
            recalculate_refundable_for_checkout(
                transaction_data.transaction, transaction_data.event
            )
            return None
    else:
        payload = generate_transaction_action_request_payload(
            transaction_data, requestor
        )
        with allow_writer():
            event_payload = EventPayload.objects.create(payload=payload)
            delivery = EventDelivery.objects.create(
                status=EventDeliveryStatus.PENDING,
                event_type=event_type,
                payload=event_payload,
                webhook=webhook,
            )
    call_event(
        handle_transaction_request_task.delay,
        delivery.id,
        transaction_data.event.id,
    )
    return None


def parse_tax_data(
    response_data: Any,
) -> Optional[TaxData]:
    try:
        return _unsafe_parse_tax_data(response_data)
    except (TypeError, KeyError, decimal.DecimalException):
        return None


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


def get_current_tax_app() -> Optional[App]:
    """Return currently used tax app or None, if there aren't any."""
    return (
        App.objects.order_by("pk")
        .filter(removed_at__isnull=True)
        .for_event_type(WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES)
        .for_event_type(WebhookEventSyncType.ORDER_CALCULATE_TAXES)
        .last()
    )


def get_meta_code_key(app: App) -> str:
    return f"{app.identifier}.code"


def get_meta_description_key(app: App) -> str:
    return f"{app.identifier}.description"


def to_payment_app_id(app: "App", external_id: str) -> "str":
    app_identifier = app.identifier or app.id
    return f"{APP_ID_PREFIX}:{app_identifier}:{external_id}"


def parse_list_payment_gateways_response(
    response_data: Any, app: "App"
) -> list["PaymentGateway"]:
    gateways: list[PaymentGateway] = []
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
