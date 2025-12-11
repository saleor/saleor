import datetime
import hashlib
import json
import logging
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from time import time
from typing import Optional
from urllib.parse import unquote, urlparse, urlunparse
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
from celery import Task
from celery.exceptions import MaxRetriesExceededError, Retry
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Count
from django.urls import reverse
from django.utils.text import slugify
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
from ...core.tasks import delete_files_from_private_storage_task
from ...core.telemetry import tracer
from ...core.utils import build_absolute_uri
from ...core.utils.url import sanitize_url_for_logging
from .. import observability
from ..const import APP_ID_PREFIX
from ..models import Webhook
from . import signature_for_payload

logger = logging.getLogger(__name__)
task_logger = get_task_logger(f"{__name__}.celery")


class WebhookSchemes(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    AWS_SQS = "awssqs"
    GOOGLE_CLOUD_PUBSUB = "gcpubsub"


@dataclass
class EventDeliveryWithAttemptCount:
    delivery: "EventDelivery"
    count: int


@dataclass
class PaymentAppData:
    app_pk: int | None
    app_identifier: str | None
    name: str


@dataclass
class WebhookResponse:
    content: str
    request_headers: dict | None = None
    response_headers: dict | None = None
    response_status_code: int | None = None
    status: str = EventDeliveryStatus.SUCCESS
    duration: float = 0.0


class RequestorModelName:
    # lowercase, as it is returned as such by `model._meta.model_name`
    APP = "app.app"
    USER = "account.user"


@dataclass
class DeferredPayloadData:
    model_name: str
    object_id: int | UUID
    requestor_model_name: str | None
    requestor_object_id: int | UUID | None
    request_time: datetime.datetime | None


def prepare_deferred_payload_data(
    subscribable_object, requestor, request_time
) -> DeferredPayloadData:
    model_name = (
        f"{subscribable_object._meta.app_label}.{subscribable_object._meta.model_name}"
    )
    requestor_model_name = (
        f"{requestor._meta.app_label}.{requestor._meta.model_name}"
        if requestor
        else None
    )
    return DeferredPayloadData(
        model_name=model_name,
        object_id=subscribable_object.pk,
        request_time=request_time,
        requestor_model_name=requestor_model_name,
        requestor_object_id=(requestor.pk if requestor else None),
    )


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


# TODO (PE-568): change typing of data to `bytes` to avoid unnecessary encoding.
def send_webhook_using_http(
    target_url,
    message,
    domain,
    signature,
    event_type,
    timeout=settings.WEBHOOK_TIMEOUT,
    custom_headers: dict[str, str] | None = None,
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
    tracer.inject_context(headers)

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
        except ClientError as e:
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
            response = future.result(
                timeout=settings.WEBHOOK_WAITING_FOR_RESPONSE_TIMEOUT
            )
        except (
            pubsub_v1.publisher.exceptions.MessageTooLargeError,
            RuntimeError,
            TimeoutError,
        ) as e:
            return WebhookResponse(content=str(e), status=EventDeliveryStatus.FAILED)
        response_duration = duration()
        return WebhookResponse(content=response, duration=response_duration)


# TODO (PE-568): change typing of data to `bytes` to avoid unnecessary encoding.
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
            "target_url": sanitize_url_for_logging(webhook.target_url),
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
        sanitize_url_for_logging(webhook.target_url),
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
            sanitize_url_for_logging(webhook.target_url),
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
            sanitize_url_for_logging(webhook.target_url),
            delivery.id,
            extra=log_extra_details,
        )
    return is_success


def get_delivery_for_webhook(
    event_delivery_id,
) -> tuple[Optional["EventDelivery"], bool]:
    delivery, inactive_delivery_ids = get_multiple_deliveries_for_webhooks(
        [event_delivery_id]
    )
    delivery = delivery.get(event_delivery_id)
    not_found = False
    if not delivery and event_delivery_id not in inactive_delivery_ids:
        not_found = True
    return delivery, not_found


def get_deliveries_for_app(
    app_id, batch_size
) -> dict[int, "EventDeliveryWithAttemptCount"]:
    deliveries = (
        EventDelivery.objects.select_related("payload", "webhook__app")
        .filter(webhook__app_id=app_id, status=EventDeliveryStatus.PENDING)
        .order_by("created_at")
        .annotate(
            attempts_count=Count("attempts", distinct=True),
        )[:batch_size]
    )

    return {
        delivery.pk: EventDeliveryWithAttemptCount(
            delivery=delivery,
            count=delivery.attempts_count,
        )
        for delivery in deliveries
    }


def get_multiple_deliveries_for_webhooks(
    event_delivery_ids,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple[dict[int, "EventDelivery"], set[int]]:
    deliveries = (
        EventDelivery.objects.using(database_connection_name)
        .select_related("payload", "webhook__app")
        .filter(id__in=event_delivery_ids)
    )

    active_deliveries = {}
    inactive_delivery_ids = set()

    not_found_delivery_ids = set(event_delivery_ids) - {
        delivery.pk for delivery in deliveries
    }
    for not_found_delivery_id in not_found_delivery_ids:
        logger.warning("Event delivery id: %r not found", not_found_delivery_id)

    for delivery in deliveries:
        if delivery.webhook.is_active and delivery.webhook.app.is_active:
            active_deliveries[delivery.pk] = delivery
        else:
            logger.info("Event delivery id: %r app/webhook is disabled.", delivery.pk)
            inactive_delivery_ids.add(delivery.pk)

    if inactive_delivery_ids:
        EventDelivery.objects.filter(id__in=inactive_delivery_ids).update(
            status=EventDeliveryStatus.FAILED
        )

    return active_deliveries, inactive_delivery_ids


@contextmanager
def catch_duration_time():
    start = time()
    yield lambda: time() - start


@allow_writer()
def create_attempt(
    delivery: "EventDelivery",
    task_id: str | None = None,
    with_save: bool = True,
):
    attempt = EventDeliveryAttempt(
        delivery=delivery,
        task_id=task_id,
        duration=None,
        response=None,
        request_headers=None,
        response_headers=None,
        status=EventDeliveryStatus.PENDING,
    )
    if with_save:
        attempt.save()
    return attempt


@allow_writer()
def attempt_update(
    attempt: "EventDeliveryAttempt",
    webhook_response: "WebhookResponse",
    with_save: bool = True,
):
    attempt.duration = webhook_response.duration
    if isinstance(webhook_response.content, str):
        attempt.response = webhook_response.content[
            : settings.EVENT_DELIVERY_ATTEMPT_RESPONSE_SIZE_LIMIT
        ]
        if attempt.response != webhook_response.content:
            attempt.response += "..."
    else:
        attempt.response = webhook_response.content
    attempt.response_headers = json.dumps(webhook_response.response_headers)
    attempt.response_status_code = webhook_response.response_status_code
    attempt.request_headers = json.dumps(webhook_response.request_headers)
    attempt.status = webhook_response.status

    if attempt.id and with_save:
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
    clear_successful_deliveries([delivery])


@allow_writer()
def clear_successful_deliveries(deliveries: list["EventDelivery"]):
    delivery_ids_to_delete = []
    payload_ids_to_delete = []
    for delivery in deliveries:
        # skip deliveries that cannot be deleted
        if not delivery.id or delivery.status != EventDeliveryStatus.SUCCESS:
            continue

        delivery_ids_to_delete.append(delivery.id)

        if payload_id := delivery.payload_id:
            payload_ids_to_delete.append(payload_id)

            payloads_to_delete = EventPayload.objects.filter(
                pk=payload_id, deliveries__isnull=True
            )

    if delivery_ids_to_delete:
        EventDelivery.objects.filter(pk__in=delivery_ids_to_delete).delete()
    if payload_ids_to_delete:
        payloads_to_delete = EventPayload.objects.filter(
            pk__in=payload_ids_to_delete, deliveries__isnull=True
        )
        files_to_delete = [
            event_payload.payload_file.name
            for event_payload in payloads_to_delete.using(
                settings.DATABASE_CONNECTION_REPLICA_NAME
            )
            if event_payload.payload_file
        ]
        payloads_to_delete.delete()
        delete_files_from_private_storage_task(files_to_delete)


@allow_writer()
def process_failed_deliveries(
    failed_deliveries_attempts: list[tuple[EventDelivery, EventDeliveryAttempt, int]],
    max_webhook_retries: int,
) -> None:
    deliveries_to_update = []
    deliveries_attempts_to_update = []
    for delivery, attempt, attempt_count in failed_deliveries_attempts:
        if attempt_count >= max_webhook_retries:
            delivery.status = EventDeliveryStatus.FAILED
            deliveries_to_update.append(delivery)
        deliveries_attempts_to_update.append(attempt)

    if deliveries_to_update:
        EventDelivery.objects.bulk_update(deliveries_to_update, ["status"])

    update_fields = [
        "duration",
        "response",
        "response_headers",
        "response_status_code",
        "request_headers",
        "status",
    ]
    if deliveries_attempts_to_update:
        EventDeliveryAttempt.objects.bulk_update(
            deliveries_attempts_to_update, update_fields
        )


@allow_writer()
def create_attempts_for_deliveries(
    deliveries: dict[int, EventDeliveryWithAttemptCount],
    task_id: str | None,
) -> dict[int, EventDeliveryAttempt]:
    attempt_for_deliveries = {}
    for delivery_id, delivery_with_count in deliveries.items():
        delivery = delivery_with_count.delivery

        attempt = create_attempt(delivery, task_id, with_save=False)
        attempt_for_deliveries[delivery_id] = attempt

    if attempt_for_deliveries:
        attempts_to_create = [
            attempt_for_deliveries[delivery_id]
            for delivery_id in attempt_for_deliveries
        ]
        EventDeliveryAttempt.objects.bulk_create(attempts_to_create)

    return attempt_for_deliveries


@allow_writer()
def delivery_update(delivery: "EventDelivery", status: str):
    delivery.status = status
    if delivery.id:
        delivery.save(update_fields=["status"])


@allow_writer()
def save_unsuccessful_delivery_attempt(attempt: "EventDeliveryAttempt"):
    delivery = attempt.delivery
    if not delivery or delivery.status == EventDeliveryStatus.SUCCESS:
        return

    event_payload = delivery.payload
    if event_payload:
        event_payload.save_as_file()

    delivery.save()
    if not attempt.id:
        attempt.save()


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


def get_meta_code_key(app: App) -> str:
    return f"{app.identifier}.code"


def get_meta_description_key(app: App) -> str:
    return f"{app.identifier}.description"


def to_payment_app_id(app: "App", external_id: str) -> "str":
    app_identifier = app.identifier or app.id
    return f"{APP_ID_PREFIX}:{app_identifier}:{external_id}"


def get_sqs_message_group_id(domain: str, app: App | None = None) -> str:
    if app is None:
        group_id = domain
    else:
        identifier = slugify(app.identifier) if app.identifier else app.id
        group_id = f"{domain}:{identifier}"
    return group_id[:128]  # SQS MessageGroupId max length is 128 chars
