import json
import logging
from dataclasses import dataclass
from enum import Enum
from json import JSONDecodeError
from typing import TYPE_CHECKING, Callable, Dict, Optional, Tuple, Type
from urllib.parse import urlparse, urlunparse

import boto3
import requests
from botocore.exceptions import ClientError
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from google.cloud import pubsub_v1
from requests.exceptions import RequestException

from ...celeryconf import app
from ...core import EventDeliveryStatus
from ...core.models import EventDelivery, EventPayload
from ...core.tracing import webhooks_opentracing_trace
from ...payment import PaymentError
from ...settings import WEBHOOK_SYNC_TIMEOUT, WEBHOOK_TIMEOUT
from ...site.models import Site
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...webhook.models import Webhook
from . import signature_for_payload
from .utils import (
    attempt_update,
    catch_duration_time,
    clear_successful_delivery,
    create_attempt,
    create_event_delivery_list_for_webhooks,
    delivery_update,
)

if TYPE_CHECKING:
    from ...app.models import App

logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)


class WebhookSchemes(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    AWS_SQS = "awssqs"
    GOOGLE_CLOUD_PUBSUB = "gcpubsub"


@dataclass
class WebhookResponse:
    content: str
    request_headers: Optional[Dict] = None
    response_headers: Optional[Dict] = None
    status: str = EventDeliveryStatus.SUCCESS
    duration: float = 0.0


def _get_webhooks_for_event(event_type, webhooks=None):
    """Get active webhooks from the database for an event."""
    permissions = {}
    required_permission = WebhookEventAsyncType.PERMISSIONS.get(
        event_type, WebhookEventSyncType.PERMISSIONS.get(event_type)
    )
    if required_permission:
        app_label, codename = required_permission.value.split(".")
        permissions["app__permissions__content_type__app_label"] = app_label
        permissions["app__permissions__codename"] = codename

    if webhooks is None:
        webhooks = Webhook.objects.all()

    webhooks = webhooks.filter(
        is_active=True,
        app__is_active=True,
        events__event_type__in=[event_type, WebhookEventAsyncType.ANY],
        **permissions,
    )
    webhooks = webhooks.select_related("app").prefetch_related(
        "app__permissions__content_type"
    )
    return webhooks


def trigger_webhooks_async(data, event_type, webhooks):
    payload = EventPayload.objects.create(payload=data)
    deliveries = create_event_delivery_list_for_webhooks(
        webhooks=webhooks,
        event_payload=payload,
        event_type=event_type,
    )
    for delivery in deliveries:
        send_webhook_request_async.delay(delivery.id)


def trigger_webhook_sync(event_type: str, data: str, app: "App"):
    """Send a synchronous webhook request."""
    webhooks = _get_webhooks_for_event(event_type, app.webhooks.all())
    webhook = webhooks.first()
    event_payload = EventPayload.objects.create(payload=data)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=event_type,
        payload=event_payload,
        webhook=webhook,
    )
    if not webhooks:
        raise PaymentError(f"No payment webhook found for event: {event_type}.")

    return send_webhook_request_sync(app.name, delivery)


def send_webhook_using_http(
    target_url, message, domain, signature, event_type, timeout=WEBHOOK_TIMEOUT
):
    """Send a webhook request using http / https protocol.

    :param target_url: Target URL request will be sent to.
    :param message: Payload that will be used.
    :param domain: Current site domain.
    :param signature: Webhook secret key checksum.
    :param event_type: Webhook event type.
    :param timeout: Request timeout.

    :return: WebhookResponse object.
    """
    headers = {
        "Content-Type": "application/json",
        # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
        "X-Saleor-Event": event_type,
        "X-Saleor-Domain": domain,
        "X-Saleor-Signature": signature,
        "Saleor-Event": event_type,
        "Saleor-Domain": domain,
        "Saleor-Signature": signature,
    }

    response = requests.post(target_url, data=message, headers=headers, timeout=timeout)
    return WebhookResponse(
        content=response.text,
        request_headers=headers,
        response_headers=dict(response.headers),
        duration=response.elapsed.total_seconds(),
        status=(
            EventDeliveryStatus.SUCCESS if response.ok else EventDeliveryStatus.FAILED
        ),
    )


def send_webhook_using_aws_sqs(target_url, message, domain, signature, event_type):
    parts = urlparse(target_url)
    region = "us-east-1"
    hostname_parts = parts.hostname.split(".")
    if len(hostname_parts) == 4 and hostname_parts[0] == "sqs":
        region = hostname_parts[1]
    client = boto3.client(
        "sqs",
        region_name=region,
        aws_access_key_id=parts.username,
        aws_secret_access_key=parts.password,
    )
    queue_url = urlunparse(
        ("https", parts.hostname, parts.path, parts.params, parts.query, parts.fragment)
    )
    is_fifo = parts.path.endswith(".fifo")

    msg_attributes = {
        "SaleorDomain": {"DataType": "String", "StringValue": domain},
        "EventType": {"DataType": "String", "StringValue": event_type},
    }
    if signature:
        msg_attributes["Signature"] = {"DataType": "String", "StringValue": signature}

    message_kwargs = {
        "QueueUrl": queue_url,
        "MessageAttributes": msg_attributes,
        "MessageBody": message.decode("utf-8"),
    }
    if is_fifo:
        message_kwargs["MessageGroupId"] = domain
    with catch_duration_time() as duration:
        response = client.send_message(**message_kwargs)
        return WebhookResponse(content=response, duration=duration())


def send_webhook_using_google_cloud_pubsub(
    target_url, message, domain, signature, event_type
):
    parts = urlparse(target_url)
    client = pubsub_v1.PublisherClient()
    topic_name = parts.path[1:]  # drop the leading slash
    with catch_duration_time() as duration:
        future = client.publish(
            topic_name,
            message,
            saleorDomain=domain,
            eventType=event_type,
            signature=signature,
        )
        response_duration = duration()
        response = future.result()
        return WebhookResponse(content=response, duration=response_duration)


def send_webhook_using_scheme_method(
    target_url, domain, secret, event_type, data
) -> WebhookResponse:
    parts = urlparse(target_url)
    message = data.encode("utf-8")
    signature = signature_for_payload(message, secret)
    scheme_matrix: Dict[
        WebhookSchemes, Tuple[Callable, Tuple[Type[Exception], ...]]
    ] = {
        WebhookSchemes.HTTP: (send_webhook_using_http, (RequestException,)),
        WebhookSchemes.HTTPS: (send_webhook_using_http, (RequestException,)),
        WebhookSchemes.AWS_SQS: (send_webhook_using_aws_sqs, (ClientError,)),
        WebhookSchemes.GOOGLE_CLOUD_PUBSUB: (
            send_webhook_using_google_cloud_pubsub,
            (pubsub_v1.publisher.exceptions.MessageTooLargeError, RuntimeError),
        ),
    }
    if method := scheme_matrix.get(parts.scheme.lower()):
        send_method, send_exception = method
        try:
            return send_method(
                target_url,
                message,
                domain,
                signature,
                event_type,
            )
        except send_exception as e:
            return WebhookResponse(content=str(e), status=EventDeliveryStatus.FAILED)
    raise ValueError("Unknown webhook scheme: %r" % (parts.scheme,))


@app.task(
    bind=True,
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def send_webhook_request_async(self, event_delivery_id):
    try:
        delivery = EventDelivery.objects.select_related("payload", "webhook__app").get(
            id=event_delivery_id
        )
    except EventDelivery.DoesNotExist:
        logger.error("Event delivery id: %r not found", event_delivery_id)
        return
    data = delivery.payload.payload
    webhook = delivery.webhook
    domain = Site.objects.get_current().domain
    attempt = create_attempt(delivery, self.request.id)
    delivery_status = EventDeliveryStatus.SUCCESS
    try:
        with webhooks_opentracing_trace(
            delivery.event_type, domain, app_name=webhook.app.name
        ):
            response = send_webhook_using_scheme_method(
                webhook.target_url,
                domain,
                webhook.secret_key,
                delivery.event_type,
                data,
            )
        attempt_update(attempt, response)
        if response.status == EventDeliveryStatus.FAILED:
            task_logger.info(
                "[Webhook ID: %r] Failed request to %r: %r for event: %r."
                " Delivery attempt id: %r",
                webhook.id,
                webhook.target_url,
                response.content,
                delivery.event_type,
                attempt.id,
            )
            try:
                countdown = self.retry_backoff * (2 ** self.request.retries)
                self.retry(countdown=countdown, **self.retry_kwargs)
            except MaxRetriesExceededError:
                task_logger.warning(
                    "[Webhook ID: %r] Failed request to %r: exceeded retry limit."
                    "Delivery id: %r",
                    webhook.id,
                    webhook.target_url,
                    delivery.id,
                )
                delivery_status = EventDeliveryStatus.FAILED
        delivery_update(delivery, delivery_status)
        task_logger.info(
            "[Webhook ID:%r] Payload sent to %r for event %r. Delivery id: %r",
            webhook.id,
            webhook.target_url,
            delivery.event_type,
            delivery.id,
        )
    except ValueError as e:
        response = WebhookResponse(content=str(e), status=EventDeliveryStatus.FAILED)
        attempt_update(attempt, response)
        delivery_update(delivery=delivery, status=EventDeliveryStatus.FAILED)
    clear_successful_delivery(delivery)


def send_webhook_request_sync(app_name, delivery):
    event_payload = delivery.payload
    data = event_payload.payload
    webhook = delivery.webhook
    parts = urlparse(webhook.target_url)
    domain = Site.objects.get_current().domain
    message = data.encode("utf-8")
    signature = signature_for_payload(message, webhook.secret_key)

    response = WebhookResponse(content="")
    response_data = None
    if parts.scheme.lower() in [WebhookSchemes.HTTP, WebhookSchemes.HTTPS]:
        logger.debug(
            "[Webhook] Sending payload to %r for event %r.",
            webhook.target_url,
            delivery.event_type,
        )
        attempt = create_attempt(delivery=delivery, task_id=None)
        try:
            with webhooks_opentracing_trace(
                delivery.event_type, domain, sync=True, app_name=app_name
            ):
                response = send_webhook_using_http(
                    webhook.target_url,
                    message,
                    domain,
                    signature,
                    delivery.event_type,
                    timeout=WEBHOOK_SYNC_TIMEOUT,
                )
                response_data = json.loads(response.content)
        except RequestException as e:
            logger.warning(
                "[Webhook] Failed request to %r: %r. "
                "ID of failed DeliveryAttempt: %r . ",
                webhook.target_url,
                e,
                attempt.id,
            )
            response.status = EventDeliveryStatus.FAILED
            if e.response:
                response.content = e.response.text
                response.response_headers = dict(e.response.headers)

        except JSONDecodeError as e:
            logger.warning(
                "[Webhook] Failed parsing JSON response from %r: %r."
                "ID of failed DeliveryAttempt: %r . ",
                webhook.target_url,
                e,
                attempt.id,
            )
            response.status = EventDeliveryStatus.FAILED
        else:
            logger.debug(
                "[Webhook] Success response from %r."
                "Succesfull DeliveryAttempt id: %r",
                webhook.target_url,
                attempt.id,
            )

        attempt_update(attempt, response)
    else:
        delivery_update(delivery, EventDeliveryStatus.FAILED)
        raise ValueError("Unknown webhook scheme: %r" % (parts.scheme,))
    delivery_update(delivery, response.status)
    clear_successful_delivery(delivery)
    return response_data


# DEPRECATED
# to be removed in task: #1q2x7xw
@app.task(compression="zlib")
def trigger_webhooks_for_event(event_type, data):
    """Send a webhook request for an event as an async task."""
    webhooks = _get_webhooks_for_event(event_type)
    for webhook in webhooks:
        send_webhook_request.delay(
            webhook.app.name,
            webhook.pk,
            webhook.target_url,
            webhook.secret_key,
            event_type,
            data,
        )


# to be removed in task: #1q2x7xw
@app.task(
    bind=True,
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
    compression="zlib",
)
def send_webhook_request(
    self, app_name, webhook_id, target_url, secret, event_type, data
):
    parts = urlparse(target_url)
    domain = Site.objects.get_current().domain
    message = data.encode("utf-8")
    signature = signature_for_payload(message, secret)

    scheme_matrix = {
        WebhookSchemes.HTTP: (send_webhook_using_http, RequestException),
        WebhookSchemes.HTTPS: (send_webhook_using_http, RequestException),
        WebhookSchemes.AWS_SQS: (send_webhook_using_aws_sqs, ClientError),
        WebhookSchemes.GOOGLE_CLOUD_PUBSUB: (
            send_webhook_using_google_cloud_pubsub,
            pubsub_v1.publisher.exceptions.MessageTooLargeError,
        ),
    }

    if methods := scheme_matrix.get(parts.scheme.lower()):
        send_method, send_exception = methods
        try:
            with webhooks_opentracing_trace(event_type, domain, app_name=app_name):
                send_method(target_url, message, domain, signature, event_type)
        except send_exception as e:
            task_logger.info("[Webhook] Failed request to %r: %r.", target_url, e)
            try:
                countdown = self.retry_backoff * (2 ** self.request.retries)
                self.retry(countdown=countdown, **self.retry_kwargs)
            except MaxRetriesExceededError:
                task_logger.warning(
                    "[Webhook] Failed request to %r: exceeded retry limit.",
                    target_url,
                )
        task_logger.info(
            "[Webhook ID:%r] Payload sent to %r for event %r",
            webhook_id,
            target_url,
            event_type,
        )
    else:
        raise ValueError("Unknown webhook scheme: %r" % (parts.scheme,))
