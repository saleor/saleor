import datetime
import json
import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Callable, Optional
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
MAX_WEBHOOK_EVENTS_IN_DB_BULK = 100


@dataclass
class WebhookPayloadData:
    subscribable_object: Any
    legacy_data_generator: Optional[Callable[[], str]] = None
    data: Optional[str] = (
        None  # deprecated, legacy_data_generator should be used instead
    )


def create_deliveries_for_multiple_subscription_objects(
    event_type,
    subscribable_objects,
    webhooks,
    requestor=None,
    allow_replica=False,
    pre_save_payloads: Optional[dict] = None,
    request_time: Optional[datetime.datetime] = None,
) -> list[EventDelivery]:
    """Create event deliveries with payloads based on multiple subscription objects.

    Trigger webhooks for each object in `subscribable_objects`. EventDeliveries and
    their related objects will be created in bulk.

    It uses a subscription query, defined for webhook to explicitly determine
    what fields should be included in the payload.

    :param event_type: event type which should be triggered.
    :param subscribable_objects: subscribable objects to process via subscription query.
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
    event_deliveries_for_bulk_update = []

    for subscribable_object in subscribable_objects:
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
                subscription_query=webhook.subscription_query,
                request=request,
                app=webhook.app,
            )

            if not data:
                logger.info(
                    "No payload was generated with subscription for event: %s",
                    event_type,
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
            event_delivery = EventDelivery(
                status=EventDeliveryStatus.PENDING,
                event_type=event_type,
                payload=event_payload,
                webhook=webhook,
            )
            event_deliveries_for_bulk_update.append(event_delivery)

            if len(event_deliveries_for_bulk_update) > MAX_WEBHOOK_EVENTS_IN_DB_BULK:
                with allow_writer():
                    # Use transaction to ensure EventPayload and EventDelivery are created together, preventing inconsistent DB state.
                    with transaction.atomic():
                        EventPayload.objects.bulk_create_with_payload_files(
                            event_payloads, event_payloads_data
                        )
                        event_deliveries.extend(
                            EventDelivery.objects.bulk_create(
                                event_deliveries_for_bulk_update
                            )
                        )
                event_payloads = []
                event_payloads_data = []
                event_deliveries_for_bulk_update = []

    with allow_writer():
        # Use transaction to ensure EventPayload and EventDelivery are created together, preventing inconsistent DB state.
        with transaction.atomic():
            EventPayload.objects.bulk_create_with_payload_files(
                event_payloads, event_payloads_data
            )
            event_deliveries.extend(
                EventDelivery.objects.bulk_create(event_deliveries_for_bulk_update)
            )
        return event_deliveries


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
    return create_deliveries_for_multiple_subscription_objects(
        event_type,
        [subscribable_object],
        webhooks,
        requestor,
        allow_replica,
        pre_save_payloads,
        request_time,
    )


def create_deliveries_for_deferred_payload_subscriptions(
    event_type: str,
    subscribable_objects,
    webhooks: Sequence["Webhook"],
    requestor=None,
    allow_replica=False,
    request_time=None,
) -> dict[int, list[tuple[EventDelivery, DeferredPayloadData]]]:
    deliveries_to_create = []
    deliveries_per_object: dict[
        int, list[tuple[EventDelivery, DeferredPayloadData]]
    ] = defaultdict(list)

    for subscribable_object in subscribable_objects:
        deferred_payload_data = prepare_deferred_payload_data(
            subscribable_object=subscribable_object,
            requestor=requestor,
            request_time=request_time,
        )

        for webhook in webhooks:
            delivery = EventDelivery(
                status=EventDeliveryStatus.PENDING,
                event_type=event_type,
                webhook=webhook,
            )
            deliveries_to_create.append(delivery)
            deliveries_per_object[subscribable_object.pk].append(
                (delivery, deferred_payload_data)
            )

    EventDelivery.objects.bulk_create(deliveries_to_create)
    return deliveries_per_object


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


def trigger_webhooks_async_for_multiple_objects(
    event_type,
    webhooks,
    webhook_payloads_data: list[WebhookPayloadData],
    requestor=None,
    allow_replica=False,
    pre_save_payloads=None,
    request_time=None,
    queue=None,
):
    """Trigger async webhooks (regular and subscription) for each object in the list.

    :param event_type: used in both webhook types as event type.
    :param webhooks: used in both webhook types, queryset of async webhooks.
    :param webhook_payloads_data: list of webhook payload data, required to generate
    the payload.
    :param requestor: used in subscription webhooks to generate metadata for payload.
    :param allow_replica: use a replica database.
    :param queue: defines the queue to which the event should be sent.
    """
    legacy_webhooks, subscription_webhooks = group_webhooks_by_subscription(webhooks)

    is_deferred_payload = WebhookEventAsyncType.EVENT_MAP.get(event_type, {}).get(
        "is_deferred_payload", False
    )

    # List of deliveries with payloads.
    deliveries: list[EventDelivery] = []

    # List of deliveries and data to generate deferred payloads for each subscribable
    # object. Note: we assume that all subscribable objects are of the same type.
    deferred_deliveries_per_object: dict[
        int, list[tuple[EventDelivery, DeferredPayloadData]]
    ] = defaultdict(list)

    for webhook_payload_detail in webhook_payloads_data:
        if legacy_webhooks:
            data = webhook_payload_detail.data
            if webhook_payload_detail.legacy_data_generator:
                data = webhook_payload_detail.legacy_data_generator()
            elif data is None:
                raise NotImplementedError(
                    "No payload was provided for regular webhooks."
                )

            with allow_writer():
                # Use transaction to ensure EventPayload and EventDelivery are created
                # together, preventing inconsistent DB state.
                with transaction.atomic():
                    payload = EventPayload.objects.create_with_payload_file(data)
                    deliveries.extend(
                        create_event_delivery_list_for_webhooks(
                            webhooks=legacy_webhooks,
                            event_payload=payload,
                            event_type=event_type,
                        )
                    )

    if subscription_webhooks:
        subscribable_objects = [
            webhook_payload_data.subscribable_object
            for webhook_payload_data in webhook_payloads_data
        ]
        if is_deferred_payload:
            deferred_deliveries_per_object = (
                create_deliveries_for_deferred_payload_subscriptions(
                    event_type=event_type,
                    subscribable_objects=subscribable_objects,
                    webhooks=subscription_webhooks,
                    requestor=requestor,
                    allow_replica=allow_replica,
                    request_time=request_time,
                )
            )
        else:
            deliveries.extend(
                create_deliveries_for_multiple_subscription_objects(
                    event_type=event_type,
                    subscribable_objects=subscribable_objects,
                    webhooks=subscription_webhooks,
                    requestor=requestor,
                    allow_replica=allow_replica,
                    pre_save_payloads=pre_save_payloads,
                    request_time=request_time,
                )
            )

    for _, deferred_deliveries in deferred_deliveries_per_object.items():
        if not deferred_deliveries:
            continue

        event_delivery_ids = [delivery.pk for delivery, _ in deferred_deliveries]

        # Deferred payload data is the same for all deliveries for a given subscribable
        # object; we can take the first one for given `deferred_deliveries`.
        deferred_payload_data = deferred_deliveries[0][1]

        # Trigger deferred payload generation task for each subscribable object.
        # This task in run on the default queue; `send_webhook_queue` is passed to
        # run the `send_webhook_request_async` task after the payload is generated.
        generate_deferred_payloads.apply_async(
            kwargs={
                "event_delivery_ids": event_delivery_ids,
                "deferred_payload_data": asdict(deferred_payload_data),
                "send_webhook_queue": queue,
            },
            bind=True,
        )

    for delivery in deliveries:
        send_webhook_request_async.apply_async(
            kwargs={"event_delivery_id": delivery.pk},
            queue=get_queue_name_for_webhook(
                delivery.webhook,
                default_queue=queue or settings.WEBHOOK_CELERY_QUEUE_NAME,
            ),
            bind=True,
            retry_backoff=10,
            retry_kwargs={"max_retries": 5},
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
    trigger_webhooks_async_for_multiple_objects(
        event_type=event_type,
        webhooks=webhooks,
        webhook_payloads_data=[
            WebhookPayloadData(
                subscribable_object=subscribable_object,
                legacy_data_generator=legacy_data_generator,
                data=data,
            )
        ],
        requestor=requestor,
        allow_replica=allow_replica,
        pre_save_payloads=pre_save_payloads,
        request_time=request_time,
        queue=queue,
    )


@app.task(bind=True)
@allow_writer()
def generate_deferred_payloads(
    self,
    event_delivery_ids: list,
    deferred_payload_data: dict,
    send_webhook_queue: Optional[str] = None,
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

    event_payloads = []
    event_payloads_data = []
    event_deliveries_for_bulk_update = []

    for delivery in deliveries:
        event_type = delivery.event_type
        webhook = delivery.webhook
        if not webhook.subscription_query:
            continue

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
            subscription_query=webhook.subscription_query,
            request=request,
            app=webhook.app,
        )

        if data_promise:
            data = data_promise.get()
            if data:
                data_json = json.dumps({**data})
                event_payloads_data.append(data_json)
                event_payload = EventPayload()
                event_payloads.append(event_payload)
                delivery.payload = event_payload
                event_deliveries_for_bulk_update.append(delivery)

    if event_deliveries_for_bulk_update:
        with allow_writer():
            with transaction.atomic():
                EventPayload.objects.bulk_create_with_payload_files(
                    event_payloads, event_payloads_data
                )
                EventDelivery.objects.bulk_update(
                    event_deliveries_for_bulk_update, ["payload"]
                )

    for delivery in event_deliveries_for_bulk_update:
        # Trigger webhook delivery task when the payload is ready.
        send_webhook_request_async.apply_async(
            kwargs={
                "event_delivery_id": delivery.pk,
            },
            queue=get_queue_name_for_webhook(
                delivery.webhook,
                default_queue=send_webhook_queue or settings.WEBHOOK_CELERY_QUEUE_NAME,
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
@allow_writer()
def send_webhook_request_async(self, event_delivery_id) -> None:
    delivery = get_delivery_for_webhook(event_delivery_id)
    if not delivery:
        return

    webhook = delivery.webhook
    domain = get_domain()
    attempt = create_attempt(delivery, self.request.id)
    delivery_status = EventDeliveryStatus.SUCCESS

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
@allow_writer()
def observability_send_events():
    with observability.opentracing_trace("send_events_task", "task"):
        if webhooks := observability.get_webhooks():
            with observability.opentracing_trace("pop_events", "buffer"):
                events, _ = observability.pop_events_with_remaining_size()
            if events:
                with observability.opentracing_trace("send_events", "webhooks"):
                    send_observability_events(webhooks, events)


@app.task(queue=OBSERVABILITY_QUEUE_NAME)
@allow_writer()
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
