import datetime
import json
import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse

from celery import group
from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.db import transaction

from ....celeryconf import app
from ....core import EventDeliveryStatus
from ....core.db.connection import allow_writer
from ....core.models import EventDelivery, EventPayload
from ....core.tracing import webhooks_opentracing_trace
from ....core.utils import get_domain
from ....graphql.core.dataloaders import DataLoader
from ....graphql.webhook.subscription_payload import (
    generate_payload_from_subscription,
    generate_payload_promise_from_subscription,
    get_pre_save_payload_key,
    initialize_request,
)
from ....graphql.webhook.subscription_types import WEBHOOK_TYPES_MAP
from ... import observability
from ...event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...observability import WebhookData
from ..utils import (
    DeferredPayloadData,
    RequestorModelName,
    WebhookResponse,
    WebhookSchemes,
    attempt_update,
    clear_successful_delivery,
    create_attempt,
    delivery_update,
    get_delivery_for_webhook,
    get_multiple_deliveries_for_webhooks,
    handle_webhook_retry,
    prepare_deferred_payload_data,
    send_webhook_using_scheme_method,
)

if TYPE_CHECKING:
    from ....webhook.models import Webhook


logger = logging.getLogger(__name__)
task_logger = get_task_logger(f"{__name__}.celery")

OBSERVABILITY_QUEUE_NAME = "observability"


def create_deliveries_for_deferred_payload_events(
    event_type: str,
    webhooks: Sequence["Webhook"],
):
    """Create a list of event deliveries for events with deferred payload.

    This flow of creating deliveries defers the payload generation to the Celery task.
    Flow can be enabled for async events by providing `is_deferred_payload=True` in
    the WebhookEventAsyncType.EVENT_MAP config.

    Note: the flow doesn't support "delete" events, as it requires model instances to
    exist in database at the time of payload generation.
    """
    event_deliveries = []
    for webhook in webhooks:
        event_deliveries.append(
            EventDelivery(
                status=EventDeliveryStatus.PENDING,
                event_type=event_type,
                webhook=webhook,
            )
        )

    with allow_writer():
        return EventDelivery.objects.bulk_create(event_deliveries)


def create_deliveries_for_subscriptions(
    event_type: str,
    subscribable_object,
    webhooks: Sequence["Webhook"],
    requestor=None,
    allow_replica=False,
    pre_save_payloads: Optional[dict] = None,
    request_time: Optional[datetime.datetime] = None,
) -> list[EventDelivery]:
    """Create a list of event deliveries with payloads based on subscription query.

    It uses a subscription query, defined for webhook to explicitly determine
    what fields should be included in the payload.

    :param event_type: event type which should be triggered.
    :param subscribable_object: subscribable object to process via subscription query.
    :param webhooks: sequence of async webhooks.
    :param requestor: used in subscription webhooks to generate meta data for payload.
    :return: List of event deliveries to send via webhook tasks.
    :param allow_replica: use replica database.
    """
    if event_type not in WEBHOOK_TYPES_MAP:
        logger.info(
            "Skipping subscription webhook. Event %s is not subscribable.", event_type
        )
        return []

    event_payloads = []
    event_payloads_data = []
    event_deliveries = []

    # Dataloaders are shared between calls to generate_payload_from_subscription to
    # reuse their cache. This avoids unnecessary DB queries when different webhooks
    # need to resolve the same data.
    dataloaders: dict[str, type[DataLoader]] = {}

    request = initialize_request(
        requestor,
        event_type in WebhookEventSyncType.ALL,
        event_type=event_type,
        allow_replica=allow_replica,
        request_time=request_time,
        dataloaders=dataloaders,
    )

    for webhook in webhooks:
        data = generate_payload_from_subscription(
            event_type=event_type,
            subscribable_object=subscribable_object,
            subscription_query=webhook.subscription_query,  # type: ignore
            request=request,
            app=webhook.app,
        )

        if not data:
            logger.info(
                "No payload was generated with subscription for event: %s", event_type
            )
            continue

        if (
            settings.ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS
            and pre_save_payloads
        ):
            key = get_pre_save_payload_key(webhook, subscribable_object)
            pre_save_payload = pre_save_payloads.get(key)
            if pre_save_payload and pre_save_payload == data:
                logger.info(
                    "[Webhook ID:%r] No data changes for event %r, skip delivery to %r",
                    webhook.id,
                    event_type,
                    webhook.target_url,
                )
                continue

        payload_data = json.dumps({**data})
        event_payloads_data.append(payload_data)
        event_payload = EventPayload()
        event_payloads.append(event_payload)
        event_deliveries.append(
            EventDelivery(
                status=EventDeliveryStatus.PENDING,
                event_type=event_type,
                payload=event_payload,
                webhook=webhook,
            )
        )

    with allow_writer():
        # Use transaction to ensure EventPayload and EventDelivery are created together, preventing inconsistent DB state.
        with transaction.atomic():
            EventPayload.objects.bulk_create_with_payload_files(
                event_payloads, event_payloads_data
            )
            return EventDelivery.objects.bulk_create(event_deliveries)


def group_webhooks_by_subscription(
    webhooks: Sequence["Webhook"],
) -> tuple[list["Webhook"], list["Webhook"]]:
    """Group webhooks by subscription query.

    Returns a tuple of two lists: legacy webhooks and subscription webhooks.
    """
    subscription = [webhook for webhook in webhooks if webhook.subscription_query]
    legacy = [webhook for webhook in webhooks if not webhook.subscription_query]
    return legacy, subscription


@allow_writer()
def create_event_delivery_list_for_webhooks(
    webhooks: Sequence["Webhook"],
    event_payload: "EventPayload",
    event_type: str,
) -> list[EventDelivery]:
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


def get_queue_name_for_webhook(webhook, default_queue):
    return {
        WebhookSchemes.AWS_SQS: settings.WEBHOOK_SQS_CELERY_QUEUE_NAME,
        WebhookSchemes.GOOGLE_CLOUD_PUBSUB: settings.WEBHOOK_PUBSUB_CELERY_QUEUE_NAME,
    }.get(
        urlparse(webhook.target_url).scheme.lower(),
        default_queue,
    )


def trigger_webhooks_async(
    data,  # deprecated, legacy_data_generator should be used instead
    event_type,
    webhooks,
    subscribable_object=None,
    requestor=None,
    legacy_data_generator=None,
    allow_replica=False,
    pre_save_payloads=None,
    request_time=None,
    queue=None,
):
    """Trigger async webhooks - both regular and subscription.

    :param data: used as payload in regular webhooks.
        Note: this is a legacy parameter, thus it is optional; if it's not provided,
        `legacy_data_generator` function is used to generate the payload when needed.
    :param event_type: used in both webhook types as event type.
    :param webhooks: used in both webhook types, queryset of async webhooks.
    :param subscribable_object: subscribable object used in subscription webhooks.
    :param requestor: used in subscription webhooks to generate metadata for payload.
    :param legacy_data_generator: used to generate payload for regular webhooks.
    :param allow_replica: use a replica database.
    :param queue: defines the queue to which the event should be sent.
    """
    legacy_webhooks, subscription_webhooks = group_webhooks_by_subscription(webhooks)

    deliveries = []
    deferred_deliveries = []

    # Legacy webhooks are those that do not have a subscription query. In this case,
    # create deliveries and the payload object on the core side, before scheduling the
    # task `send_webhook_request_async`.
    if legacy_webhooks:
        if legacy_data_generator:
            data = legacy_data_generator()
        elif data is None:
            raise NotImplementedError("No payload was provided for regular webhooks.")

        with allow_writer():
            # Use transaction to ensure EventPayload and EventDelivery are created together, preventing inconsistent DB state.
            with transaction.atomic():
                payload = EventPayload.objects.create_with_payload_file(data)
                deliveries.extend(
                    create_event_delivery_list_for_webhooks(
                        webhooks=legacy_webhooks,
                        event_payload=payload,
                        event_type=event_type,
                    )
                )

    is_deferred_payload = WebhookEventAsyncType.EVENT_MAP.get(event_type, {}).get(
        "is_deferred_payload", False
    )

    # Subscription webhooks are those that have a subscription query. Depending on the
    # `defer_payload_generation` flag, deliveries are created with or without the
    # payload. If payload generation is deferred, the payload is generated in the Celery
    # task.
    deferred_payload_data = {}
    if subscription_webhooks:
        if is_deferred_payload:
            deferred_deliveries.extend(
                create_deliveries_for_deferred_payload_events(
                    event_type=event_type, webhooks=subscription_webhooks
                )
            )
            deferred_payload_data = prepare_deferred_payload_data(
                subscribable_object, requestor, request_time
            )
        else:
            deliveries.extend(
                create_deliveries_for_subscriptions(
                    event_type=event_type,
                    subscribable_object=subscribable_object,
                    webhooks=subscription_webhooks,
                    requestor=requestor,
                    allow_replica=allow_replica,
                    pre_save_payloads=pre_save_payloads,
                    request_time=request_time,
                )
            )

    if deferred_deliveries:
        event_delivery_ids = [delivery.pk for delivery in deferred_deliveries]
        # todo: consider adding batching
        generate_deferred_payloads.apply_async(
            kwargs={
                "event_delivery_ids": event_delivery_ids,
                "deferred_payload_data": deferred_payload_data,
            }
        )

    for delivery in deliveries:
        send_webhook_request_async.apply_async(
            kwargs={
                "event_delivery_id": delivery.id,
            },
            queue=get_queue_name_for_webhook(
                delivery.webhook,
                default_queue=queue or settings.WEBHOOK_CELERY_QUEUE_NAME,
            ),
            bind=True,
            retry_backoff=10,
            retry_kwargs={"max_retries": 5},
        )


@app.task(
    queue=settings.WEBHOOK_CELERY_QUEUE_NAME,
    bind=True,
)
def generate_deferred_payloads(
    self, event_delivery_ids: list, deferred_payload_data: dict
):
    deliveries = list(get_multiple_deliveries_for_webhooks(event_delivery_ids).values())
    args_obj = DeferredPayloadData(**deferred_payload_data)
    requestor = None
    if args_obj.requestor_object_id and args_obj.requestor_model_name in (
        RequestorModelName.APP,
        RequestorModelName.USER,
    ):
        model = apps.get_model(args_obj.requestor_model_name)
        requestor = model.objects.filter(pk=args_obj.requestor_object_id).first()

    subscribable_object = (
        apps.get_model(args_obj.model_name)
        .objects.filter(pk=args_obj.object_id)
        .first()
    )
    if not subscribable_object:
        EventDelivery.objects.filter(pk__in=event_delivery_ids).update(
            status=EventDeliveryStatus.FAILED
        )
        return

    for delivery in deliveries:
        event_type = delivery.event_type
        webhook = delivery.webhook
        request = initialize_request(
            requestor,
            event_type in WebhookEventSyncType.ALL,
            event_type=event_type,
            allow_replica=True,
            request_time=args_obj.request_time,
        )
        data_promise = generate_payload_promise_from_subscription(
            event_type=event_type,
            subscribable_object=subscribable_object,
            subscription_query=webhook.subscription_query,  # type: ignore
            request=request,
            app=webhook.app,
        )

        if data_promise:
            data = data_promise.get()
            if data:
                data_json = json.dumps({**data})
                with allow_writer():
                    event_payload = EventPayload.objects.create_with_payload_file(
                        data_json
                    )
                    delivery.payload = event_payload
                    delivery.save(update_fields=["payload"])

                # Trigger webhook delivery task when the payload is ready.
                send_webhook_request_async.apply_async(
                    kwargs={
                        "event_delivery_id": delivery.id,
                    },
                    queue=get_queue_name_for_webhook(
                        delivery.webhook,
                        default_queue=settings.WEBHOOK_CELERY_QUEUE_NAME,
                    ),
                    bind=True,
                    retry_backoff=10,
                    retry_kwargs={"max_retries": 5},
                )


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
    data = None

    try:
        if not delivery.payload:
            raise ValueError(
                f"Event delivery id: %{event_delivery_id}r has no payload."
            )
        data = delivery.payload.get_payload()
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
            handle_webhook_retry(self, webhook, response, delivery, attempt)
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


def send_observability_events(webhooks: list[WebhookData], events: list[bytes]):
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
                        event,
                    )
                    if response.status == EventDeliveryStatus.FAILED:
                        failed += 1
            else:
                response = send_webhook_using_scheme_method(
                    webhook.target_url,
                    webhook.saleor_domain,
                    webhook.secret_key,
                    event_type,
                    observability.concatenate_json_events(events),
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


@app.task(queue=OBSERVABILITY_QUEUE_NAME)
def observability_send_events():
    with observability.opentracing_trace("send_events_task", "task"):
        if webhooks := observability.get_webhooks():
            with observability.opentracing_trace("pop_events", "buffer"):
                events, _ = observability.pop_events_with_remaining_size()
            if events:
                with observability.opentracing_trace("send_events", "webhooks"):
                    send_observability_events(webhooks, events)


@app.task(queue=OBSERVABILITY_QUEUE_NAME)
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
