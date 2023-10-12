import json
import logging
from typing import TYPE_CHECKING, Any, List, Sequence
from urllib.parse import urlparse

from celery import group
from celery.utils.log import get_task_logger
from django.conf import settings

from ....celeryconf import app
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....core.tracing import webhooks_opentracing_trace
from ....core.utils import get_domain
from ....graphql.webhook.subscription_payload import (
    generate_payload_from_subscription,
    initialize_request,
)
from ....graphql.webhook.subscription_types import WEBHOOK_TYPES_MAP
from ... import observability
from ...event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...observability import WebhookData
from ..utils import (
    WebhookResponse,
    WebhookSchemes,
    attempt_update,
    clear_successful_delivery,
    create_attempt,
    delivery_update,
    get_delivery_for_webhook,
    handle_webhook_retry,
    send_webhook_using_scheme_method,
)

if TYPE_CHECKING:
    from ....webhook.models import Webhook


logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)


def create_deliveries_for_subscriptions(
    event_type, subscribable_object, webhooks, requestor=None
) -> List[EventDelivery]:
    """Create a list of event deliveries with payloads based on subscription query.

    It uses a subscription query, defined for webhook to explicitly determine
    what fields should be included in the payload.

    :param event_type: event type which should be triggered.
    :param subscribable_object: subscribable object to process via subscription query.
    :param webhooks: sequence of async webhooks.
    :param requestor: used in subscription webhooks to generate meta data for payload.
    :return: List of event deliveries to send via webhook tasks.
    """
    if event_type not in WEBHOOK_TYPES_MAP:
        logger.info(
            "Skipping subscription webhook. Event %s is not subscribable.", event_type
        )
        return []

    event_payloads = []
    event_deliveries = []
    for webhook in webhooks:
        data = generate_payload_from_subscription(
            event_type=event_type,
            subscribable_object=subscribable_object,
            subscription_query=webhook.subscription_query,
            request=initialize_request(
                requestor,
                event_type in WebhookEventSyncType.ALL,
                event_type=event_type,
            ),
            app=webhook.app,
        )
        if not data:
            logger.info(
                "No payload was generated with subscription for event: %s" % event_type
            )
            continue
        event_payload = EventPayload(payload=json.dumps({**data}))
        event_payloads.append(event_payload)
        event_deliveries.append(
            EventDelivery(
                status=EventDeliveryStatus.PENDING,
                event_type=event_type,
                payload=event_payload,
                webhook=webhook,
            )
        )

    EventPayload.objects.bulk_create(event_payloads)
    return EventDelivery.objects.bulk_create(event_deliveries)


def group_webhooks_by_subscription(webhooks):
    subscription = [webhook for webhook in webhooks if webhook.subscription_query]
    regular = [webhook for webhook in webhooks if not webhook.subscription_query]

    return regular, subscription


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


def trigger_webhooks_async(
    data,  # deprecated, legacy_data_generator should be used instead
    event_type,
    webhooks,
    subscribable_object=None,
    requestor=None,
    legacy_data_generator=None,
):
    """Trigger async webhooks - both regular and subscription.

    :param data: used as payload in regular webhooks.
        Note: this is a legacy parameter, thus it is optional; if it's not provided,
        `legacy_data_generator` function is used to generate the payload when needed.
    :param event_type: used in both webhook types as event type.
    :param webhooks: used in both webhook types, queryset of async webhooks.
    :param subscribable_object: subscribable object used in subscription webhooks.
    :param requestor: used in subscription webhooks to generate meta data for payload.
    :param legacy_data_generator: used to generate payload for regular webhooks.
    """
    regular_webhooks, subscription_webhooks = group_webhooks_by_subscription(webhooks)
    deliveries = []
    if regular_webhooks:
        if legacy_data_generator:
            data = legacy_data_generator()
        elif data is None:
            raise NotImplementedError("No payload was provided for regular webhooks.")

        payload = EventPayload.objects.create(payload=data)
        deliveries.extend(
            create_event_delivery_list_for_webhooks(
                webhooks=regular_webhooks,
                event_payload=payload,
                event_type=event_type,
            )
        )
    if subscription_webhooks:
        deliveries.extend(
            create_deliveries_for_subscriptions(
                event_type=event_type,
                subscribable_object=subscribable_object,
                webhooks=subscription_webhooks,
                requestor=requestor,
            )
        )

    for delivery in deliveries:
        send_webhook_request_async.delay(delivery.id)


@app.task(
    queue=settings.WEBHOOK_CELERY_QUEUE_NAME,
    bind=True,
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def send_webhook_request_async(self, event_delivery_id):
    delivery = get_delivery_for_webhook(event_delivery_id)
    if not delivery:
        return None

    webhook = delivery.webhook
    domain = get_domain()
    attempt = create_attempt(delivery, self.request.id)
    delivery_status = EventDeliveryStatus.SUCCESS
    try:
        if not delivery.payload:
            raise ValueError(
                "Event delivery id: %r has no payload." % event_delivery_id
            )
        data = delivery.payload.payload
        with webhooks_opentracing_trace(delivery.event_type, domain, app=webhook.app):
            response = send_webhook_using_scheme_method(
                webhook.target_url,
                domain,
                webhook.secret_key,
                delivery.event_type,
                data,
                webhook.custom_headers,
            )

        attempt_update(attempt, response)
        if response.status == EventDeliveryStatus.FAILED:
            handle_webhook_retry(self, webhook, response.content, delivery, attempt)
            delivery_status = EventDeliveryStatus.FAILED
        elif response.status == EventDeliveryStatus.SUCCESS:
            task_logger.info(
                "[Webhook ID:%r] Payload sent to %r for event %r. Delivery id: %r",
                webhook.id,
                webhook.target_url,
                delivery.event_type,
                delivery.id,
            )
        delivery_update(delivery, delivery_status)
    except ValueError as e:
        response = WebhookResponse(content=str(e), status=EventDeliveryStatus.FAILED)
        attempt_update(attempt, response)
        delivery_update(delivery=delivery, status=EventDeliveryStatus.FAILED)
    observability.report_event_delivery_attempt(attempt)
    clear_successful_delivery(delivery)


def send_observability_events(webhooks: List[WebhookData], events: List[Any]):
    event_type = WebhookEventAsyncType.OBSERVABILITY
    for webhook in webhooks:
        scheme = urlparse(webhook.target_url).scheme.lower()
        failed = 0
        extra = {
            "webhook_id": webhook.id,
            "webhook_target_url": webhook.target_url,
            "events_count": len(events),
        }
        try:
            if scheme in [WebhookSchemes.AWS_SQS, WebhookSchemes.GOOGLE_CLOUD_PUBSUB]:
                for event in events:
                    response = send_webhook_using_scheme_method(
                        webhook.target_url,
                        webhook.saleor_domain,
                        webhook.secret_key,
                        event_type,
                        observability.dump_payload(event),
                    )
                    if response.status == EventDeliveryStatus.FAILED:
                        failed += 1
            else:
                response = send_webhook_using_scheme_method(
                    webhook.target_url,
                    webhook.saleor_domain,
                    webhook.secret_key,
                    event_type,
                    observability.dump_payload(events),
                )
                if response.status == EventDeliveryStatus.FAILED:
                    failed = len(events)
        except ValueError:
            logger.error(
                "Webhook ID: %r unknown webhook scheme: %r.",
                webhook.id,
                scheme,
                extra={**extra, "dropped_events_count": len(events)},
            )
            continue
        if failed:
            logger.info(
                "Webhook ID: %r failed request to %r (%s/%s events dropped): %r.",
                webhook.id,
                webhook.target_url,
                failed,
                len(events),
                response.content,
                extra={**extra, "dropped_events_count": failed},
            )
            continue
        logger.debug(
            "Successful delivered %s events to %r.",
            len(events),
            webhook.target_url,
            extra={**extra, "dropped_events_count": 0},
        )


@app.task
def observability_send_events():
    with observability.opentracing_trace("send_events_task", "task"):
        if webhooks := observability.get_webhooks():
            with observability.opentracing_trace("pop_events", "buffer"):
                events, _ = observability.pop_events_with_remaining_size()
            if events:
                with observability.opentracing_trace("send_events", "webhooks"):
                    send_observability_events(webhooks, events)


@app.task
def observability_reporter_task():
    with observability.opentracing_trace("reporter_task", "task"):
        if webhooks := observability.get_webhooks():
            with observability.opentracing_trace("pop_events", "buffer"):
                events, batch_count = observability.pop_events_with_remaining_size()
            if batch_count > 0:
                tasks = [observability_send_events.s() for _ in range(batch_count)]
                expiration = settings.OBSERVABILITY_REPORT_PERIOD.total_seconds()
                group(tasks).apply_async(expires=expiration)
            if events:
                with observability.opentracing_trace("send_events", "webhooks"):
                    send_observability_events(webhooks, events)
