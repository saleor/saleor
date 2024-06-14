import json
import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar
from urllib.parse import urlparse

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache

from ....celeryconf import app
from ....core import EventDeliveryStatus
from ....core.db.connection import allow_writer
from ....core.models import EventDelivery, EventPayload
from ....core.tracing import webhooks_opentracing_trace
from ....core.utils import get_domain
from ....graphql.webhook.subscription_payload import (
    generate_payload_from_subscription,
    initialize_request,
)
from ....graphql.webhook.subscription_types import WEBHOOK_TYPES_MAP
from ....payment.models import TransactionEvent
from ....payment.utils import (
    create_transaction_event_from_request_and_webhook_response,
    recalculate_refundable_for_checkout,
)
from ... import observability
from ...const import WEBHOOK_CACHE_DEFAULT_TIMEOUT
from ...event_types import WebhookEventSyncType
from ...utils import get_webhooks_for_event
from .. import signature_for_payload
from ..utils import (
    WebhookResponse,
    WebhookSchemes,
    attempt_update,
    clear_successful_delivery,
    create_attempt,
    delivery_update,
    generate_cache_key_for_webhook,
    get_delivery_for_webhook,
    handle_webhook_retry,
    send_webhook_using_http,
)

if TYPE_CHECKING:
    from ....webhook.models import Webhook

R = TypeVar("R")


logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)


@app.task(
    bind=True,
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def handle_transaction_request_task(self, delivery_id, request_event_id):
    request_event = TransactionEvent.objects.filter(id=request_event_id).first()
    if not request_event:
        logger.error(
            f"Cannot find the request event with id: {request_event_id} "
            f"for transaction-request webhook."
        )
        return None
    delivery = get_delivery_for_webhook(delivery_id)
    if not delivery:
        recalculate_refundable_for_checkout(request_event.transaction, request_event)
        logger.error(
            f"Cannot find the delivery with id: {delivery_id} "
            f"for transaction-request webhook."
        )
        return None
    attempt = create_attempt(delivery, self.request.id)
    response, response_data = _send_webhook_request_sync(delivery, attempt=attempt)
    if response.response_status_code and response.response_status_code >= 500:
        handle_webhook_retry(self, delivery.webhook, response, delivery, attempt)
        response_data = None
    create_transaction_event_from_request_and_webhook_response(
        request_event,
        delivery.webhook.app,
        response_data,
    )


def _send_webhook_request_sync(
    delivery, timeout=settings.WEBHOOK_SYNC_TIMEOUT, attempt=None
) -> tuple[WebhookResponse, Optional[dict[Any, Any]]]:
    event_payload = delivery.payload
    data = event_payload.payload
    webhook = delivery.webhook
    parts = urlparse(webhook.target_url)
    domain = get_domain()
    message = data.encode("utf-8")
    signature = signature_for_payload(message, webhook.secret_key)

    if parts.scheme.lower() not in [WebhookSchemes.HTTP, WebhookSchemes.HTTPS]:
        delivery_update(delivery, EventDeliveryStatus.FAILED)
        raise ValueError(f"Unknown webhook scheme: {parts.scheme!r}")

    logger.debug(
        "[Webhook] Sending payload to %r for event %r.",
        webhook.target_url,
        delivery.event_type,
    )
    if attempt is None:
        attempt = create_attempt(delivery=delivery, task_id=None)
    response = WebhookResponse(content="")
    response_data = None

    try:
        with webhooks_opentracing_trace(
            delivery.event_type, domain, sync=True, app=webhook.app
        ):
            response = send_webhook_using_http(
                webhook.target_url,
                message,
                domain,
                signature,
                delivery.event_type,
                timeout=timeout,
                custom_headers=webhook.custom_headers,
            )
            response_data = json.loads(response.content)

    except JSONDecodeError as e:
        logger.info(
            "[Webhook] Failed parsing JSON response from %r: %r."
            "ID of failed DeliveryAttempt: %r . ",
            webhook.target_url,
            e,
            attempt.id,
        )
        response.status = EventDeliveryStatus.FAILED
    else:
        if response.status == EventDeliveryStatus.FAILED:
            logger.info(
                "[Webhook] Failed request to %r: %r. "
                "ID of failed DeliveryAttempt: %r . ",
                webhook.target_url,
                response.content,
                attempt.id,
            )
        if response.status == EventDeliveryStatus.SUCCESS:
            logger.debug(
                "[Webhook] Success response from %r."
                "Successful DeliveryAttempt id: %r",
                webhook.target_url,
                attempt.id,
            )

    attempt_update(attempt, response)
    delivery_update(delivery, response.status)
    observability.report_event_delivery_attempt(attempt)
    clear_successful_delivery(delivery)
    return response, response_data


def send_webhook_request_sync(
    delivery, timeout=settings.WEBHOOK_SYNC_TIMEOUT
) -> Optional[dict[Any, Any]]:
    response, response_data = _send_webhook_request_sync(delivery, timeout)
    return response_data if response.status == EventDeliveryStatus.SUCCESS else None


def trigger_webhook_sync_if_not_cached(
    event_type: str,
    payload: str,
    webhook: "Webhook",
    cache_data: dict,
    allow_replica: bool,
    subscribable_object=None,
    request_timeout=None,
    cache_timeout=None,
    request=None,
    requestor=None,
) -> Optional[dict]:
    """Get response for synchronous webhook.

    - Send a synchronous webhook request if cache is expired.
    - Fetch response from cache if it is still valid.
    """

    cache_key = generate_cache_key_for_webhook(
        cache_data, webhook.target_url, event_type, webhook.app_id
    )
    response_data = cache.get(cache_key)
    if response_data is None:
        response_data = trigger_webhook_sync(
            event_type,
            payload,
            webhook,
            allow_replica,
            subscribable_object=subscribable_object,
            timeout=request_timeout,
            request=request,
            requestor=requestor,
        )
        if response_data is not None:
            cache.set(
                cache_key,
                response_data,
                timeout=cache_timeout or WEBHOOK_CACHE_DEFAULT_TIMEOUT,
            )
    return response_data


def create_delivery_for_subscription_sync_event(
    event_type,
    subscribable_object,
    webhook,
    requestor=None,
    request=None,
    allow_replica=False,
) -> Optional[EventDelivery]:
    """Generate webhook payload based on subscription query and create delivery object.

    It uses a defined subscription query, defined for webhook to explicitly determine
    what fields should be included in the payload.

    :param event_type: event type which should be triggered.
    :param subscribable_object: subscribable object to process via subscription query.
    :param webhook: webhook object for which delivery will be created.
    :param requestor: used in subscription webhooks to generate meta data for payload.
    :param request: used to share context between sync event calls
    :return: List of event deliveries to send via webhook tasks.
    :param allow_replica: use replica database.
    """
    if event_type not in WEBHOOK_TYPES_MAP:
        logger.info(
            "Skipping subscription webhook. Event %s is not subscribable.", event_type
        )
        return None

    if not request:
        request = initialize_request(
            requestor,
            event_type in WebhookEventSyncType.ALL,
            event_type=event_type,
            allow_replica=allow_replica,
        )
    data = generate_payload_from_subscription(
        event_type=event_type,
        subscribable_object=subscribable_object,
        subscription_query=webhook.subscription_query,
        request=request,
        app=webhook.app,
    )
    if not data:
        logger.info(
            "No payload was generated with subscription for event: %s", event_type
        )
        # Return None so if subscription query returns no data Saleor will not crash but
        # log the issue and continue without creating a delivery.
        return None

    with allow_writer():
        event_payload = EventPayload.objects.create(payload=json.dumps({**data}))
        event_delivery = EventDelivery.objects.create(
            status=EventDeliveryStatus.PENDING,
            event_type=event_type,
            payload=event_payload,
            webhook=webhook,
        )
    return event_delivery


def trigger_webhook_sync(
    event_type: str,
    payload: str,
    webhook: "Webhook",
    allow_replica,
    subscribable_object=None,
    timeout=None,
    request=None,
    requestor=None,
) -> Optional[dict[Any, Any]]:
    """Send a synchronous webhook request."""
    if webhook.subscription_query:
        delivery = create_delivery_for_subscription_sync_event(
            event_type=event_type,
            subscribable_object=subscribable_object,
            webhook=webhook,
            requestor=requestor,
            request=request,
            allow_replica=allow_replica,
        )
        if not delivery:
            return None
    else:
        with allow_writer():
            event_payload = EventPayload.objects.create(payload=payload)
            delivery = EventDelivery.objects.create(
                status=EventDeliveryStatus.PENDING,
                event_type=event_type,
                payload=event_payload,
                webhook=webhook,
            )

    kwargs = {}
    if timeout:
        kwargs = {"timeout": timeout}

    return send_webhook_request_sync(delivery, **kwargs)


def trigger_all_webhooks_sync(
    event_type: str,
    generate_payload: Callable,
    parse_response: Callable[[Any], Optional[R]],
    subscribable_object=None,
    requestor=None,
    allow_replica=False,
) -> Optional[R]:
    """Send all synchronous webhook request for given event type.

    Requests are send sequentially.
    If the current webhook does not return expected response,
    the next one is send.
    If no webhook responds with expected response,
    this function returns None.
    """
    webhooks = get_webhooks_for_event(event_type)
    request_context = None
    event_payload = None
    for webhook in webhooks:
        if webhook.subscription_query:
            if request_context is None:
                request_context = initialize_request(
                    requestor,
                    event_type in WebhookEventSyncType.ALL,
                    allow_replica,
                    event_type=event_type,
                )

            delivery = create_delivery_for_subscription_sync_event(
                event_type=event_type,
                subscribable_object=subscribable_object,
                webhook=webhook,
                request=request_context,
                requestor=requestor,
            )
            if not delivery:
                return None
        else:
            with allow_writer():
                if event_payload is None:
                    event_payload = EventPayload.objects.create(
                        payload=generate_payload()
                    )
                delivery = EventDelivery.objects.create(
                    status=EventDeliveryStatus.PENDING,
                    event_type=event_type,
                    payload=event_payload,
                    webhook=webhook,
                )

        response_data = send_webhook_request_sync(delivery)
        if parsed_response := parse_response(response_data):
            return parsed_response
    return None
