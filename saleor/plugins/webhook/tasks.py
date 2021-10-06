import logging
from enum import Enum
from json import JSONDecodeError
from typing import TYPE_CHECKING
from urllib.parse import urlparse, urlunparse

import boto3
import requests
from botocore.exceptions import ClientError
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from google.cloud import pubsub_v1
from requests.exceptions import RequestException

from ...celeryconf import app
from ...payment import PaymentError
from ...settings import WEBHOOK_SYNC_TIMEOUT, WEBHOOK_TIMEOUT
from ...site.models import Site
from ...webhook.event_types import WebhookEventType
from ...webhook.models import Webhook
from . import signature_for_payload

if TYPE_CHECKING:
    from ...app.models import App

logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)


class WebhookSchemes(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    AWS_SQS = "awssqs"
    GOOGLE_CLOUD_PUBSUB = "gcpubsub"


@app.task(compression="zlib")
def _get_webhooks_for_event(event_type, webhooks=None):
    """Get active webhooks from the database for an event."""
    permissions = {}
    required_permission = WebhookEventType.PERMISSIONS.get(event_type)
    if required_permission:
        app_label, codename = required_permission.value.split(".")
        permissions["app__permissions__content_type__app_label"] = app_label
        permissions["app__permissions__codename"] = codename

    if webhooks is None:
        webhooks = Webhook.objects.all()

    webhooks = webhooks.filter(
        is_active=True,
        app__is_active=True,
        events__event_type__in=[event_type, WebhookEventType.ANY],
        **permissions,
    )
    webhooks = webhooks.select_related("app").prefetch_related(
        "app__permissions__content_type"
    )
    return webhooks


@app.task(compression="zlib")
def trigger_webhooks_for_event(event_type, data):
    """Send a webhook request for an event as an async task."""
    webhooks = _get_webhooks_for_event(event_type)
    for webhook in webhooks:
        send_webhook_request.delay(
            webhook.pk, webhook.target_url, webhook.secret_key, event_type, data
        )


def trigger_webhook_sync(event_type: str, data: str, app: "App"):
    """Send a synchronous webhook request."""
    webhooks = _get_webhooks_for_event(event_type, app.webhooks.all())
    webhook = webhooks.first()
    if not webhook:
        raise PaymentError(f"No payment webhook found for event: {event_type}.")

    return send_webhook_request_sync(
        webhook.target_url, webhook.secret_key, event_type, data
    )


def send_webhook_using_http(
    target_url, message, domain, signature, event_type, timeout=WEBHOOK_TIMEOUT
):
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
    response.raise_for_status()
    return response


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
    client.send_message(**message_kwargs)


def send_webhook_using_google_cloud_pubsub(
    target_url, message, domain, signature, event_type
):
    parts = urlparse(target_url)
    client = pubsub_v1.PublisherClient()
    topic_name = parts.path[1:]  # drop the leading slash
    client.publish(
        topic_name,
        message,
        saleorDomain=domain,
        eventType=event_type,
        signature=signature,
    )


@app.task(
    bind=True,
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
    compression="zlib",
)
def send_webhook_request(self, webhook_id, target_url, secret, event_type, data):
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


def send_webhook_request_sync(target_url, secret, event_type, data: str):
    parts = urlparse(target_url)
    domain = Site.objects.get_current().domain
    message = data.encode("utf-8")
    signature = signature_for_payload(message, secret)

    response_data = None
    if parts.scheme.lower() in [WebhookSchemes.HTTP, WebhookSchemes.HTTPS]:
        logger.debug(
            "[Webhook] Sending payload to %r for event %r.", target_url, event_type
        )
        try:
            response = send_webhook_using_http(
                target_url,
                message,
                domain,
                signature,
                event_type,
                timeout=WEBHOOK_SYNC_TIMEOUT,
            )
            response_data = response.json()
        except RequestException as e:
            logger.debug("[Webhook] Failed request to %r: %r.", target_url, e)
        except JSONDecodeError as e:
            logger.debug(
                "[Webhook] Failed parsing JSON response from %r: %r.", target_url, e
            )
        else:
            logger.debug("[Webhook] Success response from %r.", target_url)
    else:
        raise ValueError("Unknown webhook scheme: %r" % (parts.scheme,))
    return response_data
