import logging

from celery import group
from celery.utils.log import get_task_logger
from django.conf import settings

from ...celeryconf import app
from ...core import EventDeliveryStatus
from ...core.tracing import webhooks_opentracing_trace
from ...payment.models import TransactionEvent
from ...payment.utils import create_transaction_event_from_request_and_webhook_response
from ...site.models import Site
from ...webhook import observability
from ...webhook.transport.asynchronous.transport import send_observability_events
from ...webhook.transport.synchronous.transport import _send_webhook_request_sync
from ...webhook.transport.utils import (
    WebhookResponse,
    attempt_update,
    clear_successful_delivery,
    create_attempt,
    delivery_update,
    get_delivery_for_webhook,
    handle_webhook_retry,
    send_webhook_using_scheme_method,
)

logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)


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
    domain = Site.objects.get_current().domain
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


@app.task(
    bind=True,
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def handle_transaction_request_task(self, delivery_id, request_event_id):
    delivery = get_delivery_for_webhook(delivery_id)
    if not delivery:
        logger.error(
            f"Cannot find the delivery with id: {delivery_id} "
            f"for transaction-request webhook."
        )
        return None
    request_event = TransactionEvent.objects.filter(id=request_event_id).first()
    if not request_event:
        logger.error(
            f"Cannot find the request event with id: {request_event_id} "
            f"for transaction-request webhook."
        )
        return None
    attempt = create_attempt(delivery, self.request.id)
    response, response_data = _send_webhook_request_sync(delivery, attempt=attempt)
    if response.response_status_code and response.response_status_code >= 500:
        handle_webhook_retry(
            self, delivery.webhook, response.content, delivery, attempt
        )
        response_data = None
    create_transaction_event_from_request_and_webhook_response(
        request_event,
        delivery.webhook.app,
        response_data,
    )
