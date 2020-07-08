import logging

import requests
from requests.exceptions import RequestException

from ...celeryconf import app
from ...webhook.event_types import WebhookEventType
from ...webhook.models import Webhook
from . import create_webhook_headers

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 10


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


@app.task(
    autoretry_for=(RequestException,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 15},
)
def send_webhook_request(webhook_id, target_url, secret, event_type, data):
    headers = create_webhook_headers(event_type, data, secret)
    response = requests.post(
        target_url, data=data, headers=headers, timeout=WEBHOOK_TIMEOUT
    )
    response.raise_for_status()
    logger.debug(
        f"[Webhook ID:{webhook_id}] Payload sent to {target_url} for event {event_type}"
    )
