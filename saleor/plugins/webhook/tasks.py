import json
import logging
from enum import Enum
from urllib.parse import urlparse

import requests
from google.cloud import pubsub_v1
from requests.exceptions import RequestException

from ...celeryconf import app
from ...site.models import Site
from ...webhook.event_types import WebhookEventType
from ...webhook.models import Webhook
from . import create_webhook_headers, signature_for_payload

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 10


class WebhookSchemes(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    GOOGLE_CLOUD_PUBSUB = "gcpubsub"


@app.task
def trigger_webhooks_for_event(event_type, data):
    permissions = {}
    required_permission = WebhookEventType.PERMISSIONS[event_type].value
    if required_permission:
        app_label, codename = required_permission.split(".")
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

    for webhook in webhooks:
        send_webhook_request.delay(
            webhook.pk, webhook.target_url, webhook.secret_key, event_type, data
        )


def send_webhook_using_http(target_url, secret, event_type, data):
    headers = create_webhook_headers(event_type, data, secret)
    response = requests.post(
        target_url, data=data, headers=headers, timeout=WEBHOOK_TIMEOUT
    )
    response.raise_for_status()


def send_webhook_using_google_cloud_pubsub(target_url, secret, event_type, data):
    parts = urlparse(target_url)
    client = pubsub_v1.PublisherClient()
    topic_name = parts.path[1:]  # drop the leading slash
    message = json.dumps(data).encode("utf-8")
    domain = Site.objects.get_current().domain
    signature = signature_for_payload(message, secret)
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
    if parts.scheme.lower() in [WebhookSchemes.HTTP, WebhookSchemes.HTTPS]:
        send_webhook_using_http(target_url, secret, event_type, data)
    elif parts.scheme.lower() == WebhookSchemes.GOOGLE_CLOUD_PUBSUB:
        send_webhook_using_google_cloud_pubsub(target_url, secret, event_type, data)
    else:
        raise ValueError("Unknown webhook scheme: %r" % (parts.scheme,))
    logger.debug(
        "[Webhook ID:%r] Payload sent to %r for event %r",
        webhook_id,
        target_url,
        event_type,
    )
