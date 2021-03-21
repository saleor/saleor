import logging
from enum import Enum
from urllib.parse import urlparse, urlunparse

import boto3
import requests
from google.cloud import pubsub_v1
from requests.exceptions import RequestException

from ...celeryconf import app
from ...site.models import Site
from ...webhook.event_types import WebhookEventType
from ...webhook.models import Webhook
from . import signature_for_payload

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 10


class WebhookSchemes(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    AWS_SQS = "awssqs"
    GOOGLE_CLOUD_PUBSUB = "gcpubsub"


def _get_webhooks_for_event(event_type):
    """Get active webhooks from the database for an event."""
    permissions = {}
    required_permission = WebhookEventType.PERMISSIONS.get(event_type)
    if required_permission:
        app_label, codename = required_permission.value.split(".")
        permissions["app__permissions__content_type__app_label"] = app_label
        permissions["app__permissions__codename"] = codename

    webhooks = Webhook.objects.filter(
        is_active=True,
        app__is_active=True,
        events__event_type__in=[event_type, WebhookEventType.ANY],
        **permissions,
    )
    webhooks = webhooks.select_related("app").prefetch_related(
        "app__permissions__content_type"
    )
    return webhooks


@app.task
def trigger_webhooks_for_event(event_type, data):
    """Send a webhook request for an event as an async task."""
    webhooks = _get_webhooks_for_event(event_type)
    for webhook in webhooks:
        send_webhook_request.delay(
            webhook.pk, webhook.target_url, webhook.secret_key, event_type, data
        )


def trigger_webhook_sync(webhook, event_type, data):
    """Send a synchronous webhook request."""
    response = send_webhook_request_sync(
        webhook.target_url, webhook.secret_key, event_type, data
    )
    return response


def send_webhook_using_http(target_url, message, domain, signature, event_type):
    headers = {
        "Content-Type": "application/json",
        "X-Saleor-Event": event_type,
        "X-Saleor-Domain": domain,
        "X-Saleor-Signature": signature,
    }

    response = requests.post(
        target_url, data=message, headers=headers, timeout=WEBHOOK_TIMEOUT
    )
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

    msg_attributes = {
        "SaleorDomain": {"DataType": "String", "StringValue": domain},
        "EventType": {"DataType": "String", "StringValue": event_type},
    }
    if signature:
        msg_attributes["Signature"] = {"DataType": "String", "StringValue": signature}
    client.send_message(
        QueueUrl=queue_url,
        MessageAttributes=msg_attributes,
        MessageBody=message.decode("utf-8"),
    )


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
    autoretry_for=(RequestException,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 15},
)
def send_webhook_request(webhook_id, target_url, secret, event_type, data):
    parts = urlparse(target_url)
    domain = Site.objects.get_current().domain
    message = data.encode("utf-8")
    signature = signature_for_payload(message, secret)
    if parts.scheme.lower() in [WebhookSchemes.HTTP, WebhookSchemes.HTTPS]:
        send_webhook_using_http(target_url, message, domain, signature, event_type)
    elif parts.scheme.lower() == WebhookSchemes.AWS_SQS:
        send_webhook_using_aws_sqs(target_url, message, domain, signature, event_type)
    elif parts.scheme.lower() == WebhookSchemes.GOOGLE_CLOUD_PUBSUB:
        send_webhook_using_google_cloud_pubsub(
            target_url, message, domain, signature, event_type
        )
    else:
        raise ValueError("Unknown webhook scheme: %r" % (parts.scheme,))
    logger.debug(
        "[Webhook ID:%r] Payload sent to %r for event %r",
        webhook_id,
        target_url,
        event_type,
    )


def send_webhook_request_sync(target_url, secret, event_type, data):
    parts = urlparse(target_url)
    domain = Site.objects.get_current().domain
    message = data.encode("utf-8")
    signature = signature_for_payload(message, secret)

    response = None
    if parts.scheme.lower() in [WebhookSchemes.HTTP, WebhookSchemes.HTTPS]:
        logger.debug(
            "[Webhook] Sending payload to %r for event %r.", target_url, event_type
        )
        # TODO: Handle 50x and 40x errors.
        response = send_webhook_using_http(
            target_url, message, domain, signature, event_type
        )
        logger.debug("[Webhook] Received response from %r.", target_url)
    else:
        raise ValueError("Unknown webhook scheme: %r" % (parts.scheme,))
    return response
